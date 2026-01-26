#!/usr/bin/env python
#
#  ci_cd.py
"""
Manage configuration files for continuous integration / continuous deployment.
"""
#
#  Copyright © 2020-2021 Dominic Davis-Foster <dominic@davis-foster.co.uk>
#
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
from typing import List

# 3rd party
from domdf_python_tools.paths import PathPlus
from repo_helper.templates import Environment

# this package
from project_helper.files import management

__all__ = [
		"make_github_flake8",
		"make_github_mypy",
		"ActionsManager",
		]


class ActionsManager:
	"""
	Responsible for creating, updating and removing GitHub Actions workflows.

	:param project: Path to the project root.
	:param templates:
	"""

	def __init__(self, project: pathlib.Path, templates: Environment):
		self.project = project
		self.templates = templates

		self.workflows_dir = PathPlus(project / ".github" / "workflows")
		self.workflows_dir.maybe_make(parents=True)

	def make_mypy(self) -> PathPlus:
		"""
		Create, update or remove the mypy action, as appropriate.
		"""

		ci_file = self.workflows_dir / "mypy.yml"
		template = self.templates.get_template(ci_file.name)
		ci_file.write_clean(template.render())

		return ci_file

	def make_flake8(self) -> PathPlus:
		"""
		Create, update or remove the flake8 action, as appropriate.
		"""

		ci_file = self.workflows_dir / "flake8.yml"
		template = self.templates.get_template(ci_file.name)
		ci_file.write_clean(template.render())

		return ci_file


@management.register("flake8_action", ["on_github"])
def make_github_flake8(project: pathlib.Path, templates: Environment) -> List[str]:
	"""
	Add configuration for the Flake8 GitHub Action.

	:param project: Path to the project root.
	:param templates:
	"""

	manager = ActionsManager(project, templates)

	return [manager.make_flake8().relative_to(project).as_posix()]


@management.register("mypy_action", ["on_github"])
def make_github_mypy(project: pathlib.Path, templates: Environment) -> List[str]:
	"""
	Add configuration for the mypy GitHub Action.

	:param project: Path to the project root.
	:param templates:
	"""

	# TODO: make use of the --python-version and --platform options to test all python versions and platforms in one pass
	# https://mypy.readthedocs.io/en/stable/command_line.html#cmdoption-mypy-python-version

	manager = ActionsManager(project, templates)

	return [manager.make_mypy().relative_to(project).as_posix()]
