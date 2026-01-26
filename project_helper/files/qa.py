#!/usr/bin/env python
#
#  testing.py
"""
Configuration for testing and code formatting tools.
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
from typing import Any, Dict, List

# 3rd party
import dom_toml
from domdf_python_tools.paths import PathPlus
from domdf_python_tools.stringlist import DelimitedList
from repo_helper.configupdater2 import ConfigUpdater
from repo_helper.linting import code_only_warning, lint_warn_list
from repo_helper.templates import Environment
from repo_helper.testing import standard_flake8_excludes
from repo_helper.utils import IniConfigurator, indent_join
from shippinglabel import normalize

# this package
from project_helper.files import management
from project_helper.templates import template_dir

__all__ = [
		"make_tox",
		"ToxConfig",
		"make_yapf",
		"make_formate_toml",
		"lint_warn_list",
		"make_pylintrc",
		"code_only_warning",
		]



class ToxConfig(IniConfigurator):
	"""
	Generates the ``tox.ini`` configuration file.

	:param project: Path to the project root.
	:param templates:
	"""

	filename: str = "tox.ini"
	managed_message: str = "This file is managed by 'project_helper'."
	managed_sections = [
			"tox",
			"testenv",
			"envlists",
			"testenv:lint",
			"testenv:mypy",
			"flake8",
			]

	def __init__(self, project: pathlib.Path, templates: Environment):
		self._globals = templates.globals

		self.managed_sections = self.managed_sections[:]

		for section_name in self["tox_unmanaged"]:
			if section_name in self.managed_sections:
				del self.managed_sections[self.managed_sections.index(section_name)]

		super().__init__(base_path=project)

	def __getitem__(self, item: str) -> Any:
		"""
		Passthrough to ``templates.globals``.

		:param item:
		"""

		return self._globals[item]

	def get_mypy_dependencies(self) -> List[str]:
		"""
		Compile the list of mypy dependencies.
		"""

		mypy_deps = [f"mypy=={self['mypy_version']}"]

		if (self.base_path / "stubs.txt").is_file():
			mypy_deps.append("-r{toxinidir}/stubs.txt")

		mypy_deps.extend(self["mypy_deps"])

		return mypy_deps

	def get_mypy_commands(self) -> List[str]:
		"""
		Compile the list of mypy commands.
		"""

		return [f"mypy {' '.join(self['source_files'])} {{posargs}}"]

	def tox(self) -> None:
		"""
		``[tox]``.
		"""

		self._ini["tox"]["envlist"] = ["lint", "mypy"]

	def envlists(self) -> None:
		"""
		``[envlists]``.
		"""

		self._ini["envlists"]["qa"] = ["mypy", "lint"]

	def testenv(self) -> None:
		"""
		``[testenv]``.
		"""

		self._ini["testenv"]["setenv"] = "PYTHONDEVMODE = 1"
		self._ini["testenv"]["deps"] = "importcheck>=0.1.0"
		self._ini["testenv"]["commands"] = indent_join([
				"python --version",
				"python -m importcheck {posargs}",
				])

	def testenv_lint(self) -> None:
		"""
		``[testenv:lint]``.
		"""

		self._ini["testenv:lint"]["basepython"] = "python3.8"
		self._ini["testenv:lint"]["changedir"] = "{toxinidir}"
		self._ini["testenv:lint"]["ignore_errors"] = True
		self._ini["testenv:lint"]["skip_install"] = True

		self._ini["testenv:lint"]["deps"] = indent_join([
				"flake8>=3.8.2,<5",
				"flake8-2020>=1.6.0",
				"flake8-builtins>=1.5.3",
				"flake8-docstrings>=1.5.0",
				"flake8-encodings>=0.1.0",
				"flake8-github-actions>=0.1.0",
				"git+https://github.com/python-formate/flake8-noqa.git@v1.2.2-python-formate.0",
				"flake8-pyi>=20.10.0,<=22.8.0",
				"flake8-pytest-style>=1.3.0,<2",
				"flake8-quotes>=3.3.0",
				"flake8-slots>=0.1.0",
				"flake8-sphinx-links>=0.0.4",
				"flake8-strftime>=0.1.1",
				"flake8-typing-imports>=1.10.0",
				"flake8_prettycount",
				"flake8-unused-fstrings>=2.0.0",
				"git+https://github.com/python-formate/flake8-commas.git@4.0.0-python-formate.0",
				"git+https://github.com/python-formate/flake8-unused-arguments.git@magic-methods",
				"git+https://github.com/domdfcoding/pydocstyle.git@stub-functions",
				"pygments>=2.7.1",
				])
		cmd = f"python3 -m flake8_prettycount {' '.join(self['source_files'])} {{posargs}}"
		self._ini["testenv:lint"]["commands"] = cmd

	def testenv_mypy(self) -> None:
		"""
		``[testenv:mypy]``.
		"""

		self._ini["testenv:mypy"]["basepython"] = "python3.8"
		self._ini["testenv:mypy"]["ignore_errors"] = True
		self._ini["testenv:mypy"]["skip_install"] = True
		self._ini["testenv:mypy"]["changedir"] = "{toxinidir}"
		self._ini["testenv:mypy"]["deps"] = indent_join(self.get_mypy_dependencies())
		self._ini["testenv:mypy"]["commands"] = indent_join(self.get_mypy_commands())

	def flake8(self) -> None:
		"""
		``[flake8]``.
		"""

		test_ignores = list(code_only_warning)
		test_ignores.remove("E301")
		test_ignores.remove("E302")
		test_ignores.remove("E305")

		self._ini["flake8"]["max-line-length"] = "120"
		self._ini["flake8"]["select"] = f"{DelimitedList(lint_warn_list + code_only_warning): }"
		self._ini["flake8"]["extend-exclude"] = ','.join(standard_flake8_excludes)
		self._ini["flake8"]["per-file-ignores"] = indent_join([
				'',
				f"*/*.pyi: {' '.join(str(e) for e in code_only_warning)}",
				])
		self._ini["flake8"]["pytest-parametrize-names-type"] = "csv"
		self._ini["flake8"]["inline-quotes"] = '"'
		self._ini["flake8"]["multiline-quotes"] = '"""'
		self._ini["flake8"]["docstring-quotes"] = '"""'
		self._ini["flake8"]["count"] = True
		self._ini["flake8"]["min_python_version"] = "3.4.0"
		self._ini["flake8"]["unused-arguments-ignore-abstract-functions"] = True
		self._ini["flake8"]["unused-arguments-ignore-overload-functions"] = True
		self._ini["flake8"]["unused-arguments-ignore-magic-methods"] = True
		self._ini["flake8"]["unused-arguments-ignore-variadic-names"] = True

	def merge_existing(self, ini_file: pathlib.Path) -> None:
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

						# Always put */*.pyi first
						combined_ignores_strings = [
								f"*/*.pyi: {combined_ignores.pop('*/*.pyi')}",
								*sorted(filter(bool, (map(": ".join, combined_ignores.items())))),
								]
						self._ini["flake8"]["per-file-ignores"] = indent_join(combined_ignores_strings)


@management.register("tox")
def make_tox(project: pathlib.Path, templates: Environment) -> List[str]:
	"""
	Add configuration for ``Tox``.

	https://tox.readthedocs.io

	:param project: Path to the project root.
	:param templates:
	"""

	ToxConfig(project=project, templates=templates).write_out()
	return [ToxConfig.filename]


@management.register("yapf")
def make_yapf(project: pathlib.Path, templates: Environment) -> List[str]:
	"""
	Add configuration for ``yapf``.

	https://github.com/google/yapf

	:param project: Path to the project root.
	:param templates:
	"""

	file = PathPlus(project) / ".style.yapf"
	file.write_clean(templates.get_template("style.yapf").render())
	return [file.name]


def make_formate_toml(project: pathlib.Path, templates: Environment) -> List[str]:
	"""
	Add configuration for ``formate``.

	https://formate.readthedocs.io

	:param project: Path to the project root.
	:param templates:
	"""

	known_third_party = set()

	formate_file = PathPlus(project / "formate.toml")

	isort_config = get_isort_config(project, templates)
	known_third_party.update(isort_config.get("known_third_party", {}))

	if formate_file.is_file():
		formate_config = dom_toml.load(formate_file)
	else:
		formate_config = {}

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

	formate_file = PathPlus(project / "formate.toml")
	dom_toml.dump(formate_config, formate_file, encoder=dom_toml.TomlEncoder)

	return [formate_file.name]


def get_isort_config(project: pathlib.Path, templates: Environment) -> Dict[str, Any]:
	"""
	Returns a ``key: value`` mapping of configuration for ``isort``.

	https://github.com/timothycrosley/isort

	:param project: Path to the project root.
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

	# Update from the adafruit/circuitpython repository
	# docs/shared_bindings_matrix.py
	# >>> shared_bindings_matrix.get_shared_bindings()
	isort["extra_standard_library"] = [
			"usb_hid",
			"network",
			"wifi",
			"board",
			"_pew",
			"gnss",
			"i2cperipheral",
			"pulseio",
			"storage",
			"pwmio",
			"neopixel_write",
			"audiobusio",
			"bitops",
			"audiocore",
			"fontio",
			"analogio",
			"sdioio",
			"_eve",
			"bitbangio",
			"framebufferio",
			"gamepad",
			"uheap",
			"_bleio",
			"rgbmatrix",
			"rtc",
			"alarm",
			"nvm",
			"camera",
			"aesio",
			"dualbank",
			"sdcardio",
			"socketpool",
			"audiomp3",
			"bitmaptools",
			"frequencyio",
			"usb_midi",
			"supervisor",
			"usb_cdc",
			"displayio",
			"memorymonitor",
			"_stage",
			"touchio",
			"_pixelbuf",
			"audiomixer",
			"sharpdisplay",
			"msgpack",
			"terminalio",
			"countio",
			"_typing",
			"audiopwmio",
			"digitalio",
			"multiterminal",
			"audioio",
			"ps2io",
			"rotaryio",
			"microcontroller",
			"busio",
			"vectorio",
			"wiznet",
			"watchdog",
			"canio",
			"ustack",
			"gamepadshift",
			"binascii",
			"errno",
			"ulab",
			]

	return isort







@management.register("pylintrc")
def make_pylintrc(project: pathlib.Path, templates: Environment) -> List[str]:
	"""
	Copy ``.pylintrc`` into the desired repository.

	:param project: Path to the project root.
	:param templates:
	"""

	file = PathPlus(project / ".pylintrc")
	file.write_clean(PathPlus(template_dir / "pylintrc").read_text())
	return [file.name]
