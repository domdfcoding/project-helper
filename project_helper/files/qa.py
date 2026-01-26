#!/usr/bin/env python
#
#  testing.py
"""
Configuration for testing and code formatting tools.
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
import os.path
import pathlib
import posixpath
import re
import warnings
from operator import attrgetter
from typing import Any, Dict, List, Tuple

# 3rd party
import dom_toml
from domdf_python_tools.paths import PathPlus
from domdf_python_tools.stringlist import DelimitedList
from domdf_python_tools.typing import PathLike
from packaging.version import Version
from shippinglabel import normalize
from shippinglabel.requirements import (
		ComparableRequirement,
		RequirementsManager,
		combine_requirements,
		read_requirements
		)

# this package
from repo_helper.configupdater2 import ConfigUpdater
from repo_helper.files import management
from repo_helper.files.linting import code_only_warning, lint_warn_list
from repo_helper.templates import Environment
from repo_helper.utils import IniConfigurator, indent_join

__all__ = [
		"make_tox",
		"ToxConfig",
		"make_yapf",
		"make_formate_toml",
		]

allowed_rst_directives = ["envvar", "TODO", "extras-require", "license", "license-info"]
allowed_rst_roles = ["choosealicense"]
standard_flake8_excludes = [
		"old",
		"build",
		"dist",
		"__pkginfo__.py",
		"setup.py",
		"venv",
		]


class ToxConfig(IniConfigurator):
	"""
	Generates the ``tox.ini`` configuration file.

	:param repo_path: Path to the repository root.
	:param templates:
	"""

	filename: str = "tox.ini"
	managed_sections = [
			"tox",
			"testenv",
			"testenv:lint",
			"testenv:mypy",
			"flake8",
			"check-wheel-contents",
			]

	def __init__(self, repo_path: pathlib.Path, templates: Environment):
		self._globals = templates.globals

		self.managed_sections = self.managed_sections[:]

		for section_name in self["tox_unmanaged"]:
			if section_name in self.managed_sections:
				del self.managed_sections[self.managed_sections.index(section_name)]

		super().__init__(base_path=repo_path)

	def __getitem__(self, item: str) -> Any:
		"""
		Passthrough to ``templates.globals``.

		:param item:
		"""

		return self._globals[item]

	def get_source_files(self) -> List[str]:
		"""
		Compile the list of source files.
		"""

		return [posixpath.join(self._globals["source_dir"], self._globals["import_name"].replace('.', '/'))]

	def get_mypy_dependencies(self) -> List[str]:
		"""
		Compile the list of mypy dependencies.
		"""

		mypy_deps = [f"mypy=={self['mypy_version']}"]

		# mypy_deps.append("lxml")

		if self._globals["enable_tests"]:
			mypy_deps.append(f"-r{{toxinidir}}/{self._globals['tests_dir']}/requirements.txt")

		if (self.base_path / "stubs.txt").is_file():
			mypy_deps.append("-r{toxinidir}/stubs.txt")

		mypy_deps.extend(self._globals["mypy_deps"])

		return mypy_deps

	def get_mypy_commands(self) -> List[str]:
		"""
		Compile the list of mypy commands.
		"""

		return [f"mypy {' '.join(self.get_source_files())} {{posargs}}"]

	def tox(self):
		"""
		``[tox]``.
		"""

		self._ini["tox"]["envlist"] = ["lint", "mypy"]
		self._ini["tox"]["requires"] = indent_join(sorted(tox_requires))

	def testenv(self):
		"""
		``[testenv]``.
		"""

		self._ini["testenv"]["setenv"] = "PYTHONDEVMODE = 1"
		self._ini["testenv"]["deps"] = "importcheck>=0.1.0"
		self._ini["testenv"]["commands"] = indent_join([
				"python --version",
				"python -m importcheck {posargs}",
				])

	def testenv_lint(self):
		"""
		``[testenv:lint]``.
		"""

		self._ini["testenv:lint"]["basepython"] = "python{python_deploy_version}".format(**self._globals)
		self._ini["testenv:lint"]["changedir"] = "{toxinidir}"
		self._ini["testenv:lint"]["ignore_errors"] = True
		self._ini["testenv:lint"]["skip_install"] = True

		self._ini["testenv:lint"]["deps"] = indent_join([
				"flake8>=3.8.2",
				"flake8-2020>=1.6.0",
				"flake8-builtins>=1.5.3",
				"flake8-docstrings>=1.5.0",
				"flake8-dunder-all>=0.1.1",
				"flake8-encodings>=0.1.0",
				"flake8-github-actions>=0.1.0",
				"flake8-noqa>=1.1.0",
				"flake8-pyi>=20.10.0",
				"flake8-pytest-style>=1.3.0",
				"flake8-quotes>=3.3.0",
				"flake8-slots>=0.1.0",
				"flake8-sphinx-links>=0.0.4",
				"flake8-strftime>=0.1.1",
				"flake8-typing-imports>=1.10.0",
				"git+https://github.com/domdfcoding/flake8-rst-docstrings-sphinx.git",
				"git+https://github.com/domdfcoding/flake8-rst-docstrings.git",
				"git+https://github.com/python-formate/flake8-unused-arguments.git@magic-methods",
				"pydocstyle>=6.0.0",
				"pygments>=2.7.1",
				"importlib_metadata<4.5.0; python_version<'3.8'"
				])
		cmd = f"python3 -m flake8_rst_docstrings_sphinx {' '.join(self.get_source_files())} --allow-toolbox {{posargs}}"
		self._ini["testenv:lint"]["commands"] = cmd

	def testenv_mypy(self):
		"""
		``[testenv:mypy]``.
		"""

		self._ini["testenv:mypy"]["basepython"] = "python{python_deploy_version}".format(**self._globals)
		self._ini["testenv:mypy"]["ignore_errors"] = True
		self._ini["testenv:mypy"]["skip_install"] = True
		self._ini["testenv:mypy"]["changedir"] = "{toxinidir}"

		if self._globals["tox_testenv_extras"]:
			self._ini["testenv:mypy"]["extras"] = self._globals["tox_testenv_extras"]

		self._ini["testenv:mypy"]["deps"] = indent_join(self.get_mypy_dependencies())

		commands = self.get_mypy_commands()

		if commands:
			self._ini["testenv:mypy"]["commands"] = indent_join(commands)
		else:
			self._ini.remove_section("testenv:mypy")

	def flake8(self):
		"""
		``[flake8]``.
		"""

		self._ini["flake8"]["max-line-length"] = "120"
		self._ini["flake8"]["select"] = f"{DelimitedList(lint_warn_list + code_only_warning): }"
		self._ini["flake8"]["extend-exclude"] = ','.join([self["docs_dir"], *standard_flake8_excludes])
		self._ini["flake8"]["per-file-ignores"] = indent_join([
				'',
				f"*/*.pyi: {' '.join(str(e) for e in code_only_warning)}",
				])
		self._ini["flake8"]["pytest-parametrize-names-type"] = "csv"
		self._ini["flake8"]["inline-quotes"] = '"'
		self._ini["flake8"]["multiline-quotes"] = '"""'
		self._ini["flake8"]["docstring-quotes"] = '"""'
		self._ini["flake8"]["count"] = True
		self._ini["flake8"]["min_python_version"] = self["requires_python"]
		self._ini["flake8"]["unused-arguments-ignore-abstract-functions"] = True
		self._ini["flake8"]["unused-arguments-ignore-overload-functions"] = True
		self._ini["flake8"]["unused-arguments-ignore-magic-methods"] = True
		self._ini["flake8"]["unused-arguments-ignore-variadic-names"] = True

	def check_wheel_contents(self):
		"""
		``[check-wheel-contents]``.
		"""

		self._ini["check-wheel-contents"]["ignore"] = "W002"

		if self["py_modules"]:
			self._ini["check-wheel-contents"]["toplevel"] = "{import_name}.py".format(**self._globals)
		elif self["stubs_package"]:
			self._ini["check-wheel-contents"]["toplevel"] = "{import_name}-stubs".format(**self._globals)

			if self["pure_python"]:
				# Don't check contents for packages with binary extensions
				stubs_dir = f"{os.path.join(self['source_dir'], self['import_name'])}-stubs"
				self._ini["check-wheel-contents"]["package"] = stubs_dir

		else:
			self._ini["check-wheel-contents"]["toplevel"] = f"{self['import_name'].split('.')[0]}"

			if self["pure_python"]:
				# Don't check contents for packages with binary extensions
				self._ini["check-wheel-contents"]["package"] = os.path.join(
						self["source_dir"],
						self["import_name"].split('.')[0],
						)

	def pytest(self):
		"""
		``[pytest]``.
		"""

		if self["enable_tests"]:
			self._ini["pytest"]["addopts"] = "--color yes --durations 25"
			# --reruns 1 --reruns-delay 5
			self._ini["pytest"]["timeout"] = 300
		else:
			self._ini.remove_section("pytest")

	def merge_existing(self, ini_file):
		"""
		Merge existing sections in the configuration file into the new configuration.

		:param ini_file: The existing ``.ini`` file.
		"""

		if ini_file.is_file():
			existing_config = ConfigUpdater()
			existing_config.read(str(ini_file))

			for section in existing_config.sections_blocks():
				if section.name not in self.managed_sections:
					self._ini.add_section(section)
				elif section.name == "flake8":

					if "per-file-ignores" in section:
						combined_ignores = {}

						# Existing first, so they're always overridden by our new ones
						for line in section["per-file-ignores"].value.splitlines():
							if not line.strip():
								continue
							glob, ignores = line.split(':', 1)
							combined_ignores[glob.strip()] = ignores.strip()

						for line in self._ini["flake8"]["per-file-ignores"].value.splitlines():
							if not line.strip():
								continue
							glob, ignores = line.split(':', 1)
							combined_ignores[glob.strip()] = ignores.strip()

						# Always put tests/* and */*.pyi first
						combined_ignores_strings = [
								f"tests/*: {combined_ignores.pop('tests/*')}",
								f"*/*.pyi: {combined_ignores.pop('*/*.pyi')}",
								]

						combined_ignores_strings.extend(
								sorted(filter(bool, (map(": ".join, combined_ignores.items()))))
								)
						self._ini["flake8"]["per-file-ignores"] = indent_join(combined_ignores_strings)


@management.register("tox")
def make_tox(repo_path: pathlib.Path, templates: Environment) -> List[str]:
	"""
	Add configuration for ``Tox``.

	https://tox.readthedocs.io

	:param repo_path: Path to the repository root.
	:param templates:
	"""

	ToxConfig(repo_path=repo_path, templates=templates).write_out()
	return [ToxConfig.filename]


@management.register("yapf")
def make_yapf(repo_path: pathlib.Path, templates: Environment) -> List[str]:
	"""
	Add configuration for ``yapf``.

	https://github.com/google/yapf

	:param repo_path: Path to the repository root.
	:param templates:
	"""

	file = PathPlus(repo_path) / ".style.yapf"
	file.write_clean(templates.get_template("style.yapf").render())
	return [file.name]


def make_formate_toml(repo_path: pathlib.Path, templates: Environment) -> List[str]:
	"""
	Add configuration for ``formate``.

	https://formate.readthedocs.io

	:param repo_path: Path to the repository root.
	:param templates:
	"""

	known_third_party = set()

	isort_file = PathPlus(repo_path / ".isort.cfg")
	formate_file = PathPlus(repo_path / "formate.toml")

	isort_config = get_isort_config(repo_path, templates)
	known_third_party.update(isort_config["known_third_party"])

	if formate_file.is_file():
		formate_config = dom_toml.load(formate_file)
	else:
		formate_config = {}

	# Read the isort config file and get "known_third_party" from there
	if isort_file.is_file():
		isort = ConfigUpdater()
		isort.read(str(isort_file))

		if "settings" in isort.sections() and "known_third_party" in isort["settings"]:
			known_third_party.update(re.split(r"(\n|,\s*)", isort["settings"]["known_third_party"].value))

	isort_file.unlink(missing_ok=True)

	if "hooks" in formate_config and "isort" in formate_config["hooks"]:
		if "kwargs" in formate_config["hooks"]["isort"]:
			known_third_party.update(formate_config["hooks"]["isort"]["kwargs"].get("known_third_party", ()))

			for existing_key, value in formate_config["hooks"]["isort"]["kwargs"].items():
				if existing_key not in isort_config:
					isort_config[existing_key] = value

	def normalise_underscore(name: str) -> str:
		return normalize(name.strip()).replace('-', '_')

	isort_config["known_third_party"] = sorted(set(filter(bool, map(normalise_underscore, known_third_party))))

	hooks = {
			"dynamic_quotes": 10,
			"collections-import-rewrite": 20,
			"yapf": {"priority": 30, "kwargs": {"yapf_style": ".style.yapf"}},
			"reformat-generics": 40,
			"isort": {"priority": 50, "kwargs": isort_config},
			"noqa-reformat": 60,
			"ellipsis-reformat": 70,
			"squish_stubs": 80,
			}

	config = {"indent": '\t', "line_length": 115}

	formate_config["hooks"] = hooks
	formate_config["config"] = config

	formate_file = PathPlus(repo_path / "formate.toml")
	dom_toml.dump(formate_config, formate_file, encoder=dom_toml.TomlEncoder)

	return [formate_file.name, isort_file.name]


def get_isort_config(repo_path: pathlib.Path, templates: Environment) -> Dict[str, Any]:
	"""
	Returns a ``key: value`` mapping of configuration for ``isort``.

	https://github.com/timothycrosley/isort

	:param repo_path: Path to the repository root.
	:param templates:
	"""

	isort: Dict[str, Any] = {}

	isort["indent"] = "\t\t"  # To match what yapf uses

	# Undocumented 8th option with the closing bracket indented
	isort["multi_line_output"] = 8
	isort["import_heading_stdlib"] = "stdlib"
	isort["import_heading_thirdparty"] = "3rd party"
	isort["import_heading_firstparty"] = "this package"
	isort["import_heading_localfolder"] = "this package"
	isort["balanced_wrapping"] = False
	isort["lines_between_types"] = 0
	isort["use_parentheses"] = True
	isort["remove_redundant_aliases"] = True
	isort["default_section"] = "THIRDPARTY"
	# TODO: circuitpython builtin libraries as first party

	if templates.globals["enable_tests"]:
		test_requirements = read_requirements(
				repo_path / templates.globals["tests_dir"] / "requirements.txt",
				include_invalid=True,
				)[0]
	else:
		test_requirements = set()

	main_requirements = read_requirements(repo_path / "requirements.txt")[0]

	all_requirements = set(map(normalize, map(attrgetter("name"), (*test_requirements, *main_requirements))))
	all_requirements.discard(templates.globals["import_name"])
	all_requirements.discard("iniconfig")

	known_third_party = [req.replace('-', '_') for req in sorted(all_requirements)]
	isort["known_third_party"] = known_third_party
	isort["known_first_party"] = templates.globals["import_name"]

	return isort
