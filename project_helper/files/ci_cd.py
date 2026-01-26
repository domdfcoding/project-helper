#!/usr/bin/env python
#
#  ci_cd.py
"""
Manage configuration files for continuous integration / continuous deployment.
"""
#
#  Copyright © 2020-2021 Dominic Davis-Foster <dominic@davis-foster.co.uk>
#  Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"), to deal
#  in the Software without restriction, including without limitation the rights
#  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#  copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in all
#  copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
#  EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
#  MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#  IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
#  DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
#  OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE
#  OR OTHER DEALINGS IN THE SOFTWARE.
#

# stdlib
import pathlib
import posixpath
from textwrap import indent
from typing import Dict, Iterator, List, Optional, Tuple

# 3rd party
from domdf_python_tools.paths import PathPlus
from domdf_python_tools.stringlist import DelimitedList, StringList
from packaging.version import InvalidVersion, Version

# this package
from repo_helper.files import management
from repo_helper.templates import Environment
from repo_helper.utils import set_gh_actions_versions

__all__ = [
		"make_github_flake8",
		"make_github_mypy",
		"ActionsManager",
		]


class ActionsManager:
	"""
	Responsible for creating, updating and removing GitHub Actions workflows.

	:param repo_path: Path to the repository root.
	:param templates:
	"""

	def __init__(self, repo_path: pathlib.Path, templates: Environment):
		self.repo_path = repo_path
		self.templates = templates

		self.actions = templates.get_template("github_ci.yml")

		self.workflows_dir = PathPlus(repo_path / ".github" / "workflows")
		self.workflows_dir.maybe_make(parents=True)

		code_file_filter: DelimitedList[str] = DelimitedList()

		if self.templates.globals["enable_docs"]:
			code_file_filter.append(f"{templates.globals['docs_dir']}/**")
		else:
			code_file_filter.append(f"doc-source/**")

		code_file_filter.extend([
				"CONTRIBUTING.rst",
				".imgbotconfig",
				".pre-commit-config.yaml",
				".pylintrc",
				".readthedocs.yml",
				])
		# ".bumpversion.cfg",
		# ".style.yapf",
		# "stubs.txt",

		self._code_file_filter = f"!({code_file_filter:|})"

	def make_mypy(self) -> PathPlus:
		"""
		Create, update or remove the mypy action, as appropriate.

		.. versionadded:: 2020.1.27
		"""

		ci_file = self.workflows_dir / "mypy.yml"
		template = self.templates.get_template(ci_file.name)
		dependency_lines = self.get_linux_mypy_requirements()

		dependencies_block = StringList([
				"- name: Install dependencies 🔧",
				f"  if: ${{{{ matrix.os == 'ubuntu-20.04' && steps.changes.outputs.code == 'true' }}}}",
				"  run: |",
				])
		with dependencies_block.with_indent("  ", 2):
			dependencies_block.extend(dependency_lines)

		ci_file.write_clean(
				template.render(
						platforms=["Linux"],
						linux_platform="ubuntu-20.04",
						dependencies_block=indent(str(dependencies_block), "      "),
						code_file_filter=self._code_file_filter,
						)
				)

		return ci_file

	def make_flake8(self) -> PathPlus:
		"""
		Create, update or remove the flake8 action, as appropriate.

		.. versionadded:: 2021.8.11
		"""

		ci_file = self.workflows_dir / "flake8.yml"
		template = self.templates.get_template(ci_file.name)
		# TODO: handle case where Linux is not a supported platform

		ci_file.write_clean(template.render(code_file_filter=self._code_file_filter))

		return ci_file

	def get_linux_mypy_requirements(self) -> List[str]:
		"""
		Returns the Python requirements to run tests for on Linux.
		"""

		return [
				"python -VV",
				"python -m site",
				"python -m pip install --upgrade pip setuptools wheel",
				"python -m pip install --upgrade tox virtualenv",
				]


@management.register("flake8_action")
def make_github_flake8(repo_path: pathlib.Path, templates: Environment) -> List[str]:
	"""
	Add configuration for the Flake8 GitHub Action.

	:param repo_path: Path to the repository root.
	:param templates:
	"""

	manager = ActionsManager(repo_path, templates)

	return [manager.make_flake8().relative_to(repo_path).as_posix()]


@management.register("mypy_action")
def make_github_mypy(repo_path: pathlib.Path, templates: Environment) -> List[str]:
	"""
	Add configuration for the mypy GitHub Action.

	:param repo_path: Path to the repository root.
	:param templates:
	"""

	# TODO: make use of the --python-version and --platform options to test all python versions and platforms in one pass
	# https://mypy.readthedocs.io/en/stable/command_line.html#cmdoption-mypy-python-version

	manager = ActionsManager(repo_path, templates)

	return [manager.make_mypy().relative_to(repo_path).as_posix()]


def get_init_filename(templates: Environment) -> Optional[str]:
	if templates.globals["py_modules"]:
		for modname in templates.globals["py_modules"]:
			return f"{templates.globals['source_dir']}{modname}.py"
	elif not templates.globals["stubs_package"]:
		source_dir = posixpath.join(
				templates.globals["source_dir"],
				templates.globals["import_name"].replace('.', '/'),
				)
		return f"{source_dir}/__init__.py"

	return None
