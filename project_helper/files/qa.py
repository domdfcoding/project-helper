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
from repo_helper.templates import Environment
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
				"flake8>=3.8.2",
				"flake8-2020>=1.6.0",
				"flake8-builtins>=1.5.3",
				"flake8-docstrings>=1.5.0",
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
				"flake8_prettycount",
				"git+https://github.com/python-formate/flake8-unused-arguments.git@magic-methods",
				"pydocstyle>=6.0.0",
				"pygments>=2.7.1",
				"importlib_metadata<4.5.0; python_version<'3.8'",
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


lint_warn_list = [
		"E111",
		"E112",
		"E113",
		"E121",
		"E122",
		"E125",
		"E127",
		"E128",
		"E129",
		"E131",
		"E133",
		"E201",
		"E202",
		"E203",
		"E211",
		"E222",
		"E223",
		"E224",
		"E225",
		"E225",
		"E226",
		"E227",
		"E228",
		"E231",
		"E241",
		"E242",
		"E251",
		"E261",
		"E262",
		"E265",
		"E271",
		"E272",
		"E303",
		"E304",
		"E306",
		"E402",
		"E502",
		"E703",
		"E711",
		"E712",
		"E713",
		"E714",
		"E721",
		"W291",
		"W292",
		"W293",
		"W391",
		"W504",
		]

# flake8_2020
lint_warn_list.extend((
		"YTT101",  # sys.version[:3] referenced (python3.10)
		"YTT102",  # sys.version[2] referenced (python3.10)
		"YTT103",  # sys.version compared to string (python3.10)
		"YTT201",  # sys.version_info[0] == 3 referenced (python4)
		"YTT202",  # six.PY3 referenced (python4)
		"YTT203",  # sys.version_info[1] compared to integer (python4)
		"YTT204",  # sys.version_info.minor compared to integer (python4)
		"YTT301",  # sys.version[0] referenced (python10)
		"YTT302",  # sys.version compared to string (python10)
		"YTT303",  # sys.version[:1] referenced (python10)
		))

# flake8_strftime
lint_warn_list.extend((
		"STRFTIME001",  # Linux-specific strftime code used
		"STRFTIME002",  # Windows-specific strftime code used
		))

# flake8_pytest
lint_warn_list.extend((
		"PT001",  # use @pytest.fixture() over @pytest.fixture (configurable by pytest-fixture-no-parentheses)
		"PT002",  # configuration for fixture '{name}' specified via positional args, use kwargs
		"PT003",  # scope='function' is implied in @pytest.fixture()
		"PT006",  # wrong name(s) type in @pytest.mark.parametrize
		"PT007",  # wrong values type in @pytest.mark.parametrize
		"PT008",  # use return_value= instead of patching with lambda
		"PT009",  # use a regular assert instead of unittest-style '{assertion}'
		"PT010",  # set the expected exception in pytest.raises()
		"PT011",  # set the match parameter in pytest.raises.
		"PT012",  # pytest.raises() block should contain a single simple statement
		"PT013",  # found incorrect import of pytest, use simple 'import pytest' instead
		"PT014",  # found duplicate test cases {indexes} in @pytest.mark.parametrize
		"PT015",  # assertion always fails, replace with pytest.fail()
		"PT016",  # no message passed to pytest.fail()
		"PT017",  # found assertion on exception {name} in except block, use pytest.raises() instead
		"PT018",  # assertion should be broken down into multiple parts
		"PT019",  # fixture {name} without value is injected as parameter, use @pytest.mark.usefixtures instead
		"PT020",  # @pytest.yield_fixture is deprecated, use @pytest.fixture
		"PT021",  # use yield instead of request.addfinalizer
		))

# flake8-quotes
lint_warn_list.extend((
		"Q001",  # Remove bad quotes from multiline string
		"Q002",  # Remove bad quotes from docstring
		"Q003",  # Change outer quotes to avoid escaping inner quotes
		))

# flake8-builtins
lint_warn_list.extend((
		"A001",  # variable "{0}" is shadowing a python builtin
		"A002",  # argument "{0}" is shadowing a python builtin
		"A003",  # class attribute "{0}" is shadowing a python builtin
		))

# Type checking
lint_warn_list.extend((
		"TYP001",  # guard import by TYPE_CHECKING
		"TYP002",  # @overload is broken in <3.5.2
		"TYP003",  # Union[Match, ...] or Union[Pattern, ...] must be quoted in <3.5.2
		"TYP004",  # NamedTuple does not support methods in 3.6.0
		"TYP005",  # NamedTuple does not support defaults in 3.6.0
		"TYP006",  # guard typing attribute by quoting
		))

# Encodings
lint_warn_list.extend((
		"ENC001",  # no encoding specified for 'open'.
		"ENC002",  # 'encoding=None' used for 'open'.
		"ENC003",  # no encoding specified for 'open' with unknown mode.
		"ENC004",  # 'encoding=None' used for 'open' with unknown mode.
		"ENC011",  # no encoding specified for 'configparser.ConfigParser.read'.
		"ENC012",  # 'encoding=None' used for 'configparser.ConfigParser.read'.
		"ENC021",  # no encoding specified for ‘pathlib.Path.open’.
		"ENC022",  # ’encoding=None’ used for ‘pathlib.Path.open’.
		"ENC023",  # no encoding specified for ‘pathlib.Path.read_text’.
		"ENC024",  # ’encoding=None’ used for ‘pathlib.Path.read_text’.
		"ENC025",  # no encoding specified for ‘pathlib.Path.write_text’.
		"ENC026",  # ’encoding=None’ used for ‘pathlib.Path.write_text’."""
		))

# pydocstyle
code_only_warning = [
		"E301",
		"E302",
		"E305",
		"D100",  # Missing docstring in public module
		"D101",  # Missing docstring in public class
		"D102",  # Missing docstring in public method
		"D103",  # Missing docstring in public function
		"D104",  # Missing docstring in public package
		# "D105",  # Missing docstring in magic method
		"D106",  # Missing docstring in public nested class
		# "D107",  # Missing docstring in __init__
		"D201",  # No blank lines allowed before function docstring
		"D204",  # 1 blank line required after class docstring
		"D207",  # Docstring is under-indented
		"D208",  # Docstring is over-indented
		"D209",  # Multi-line docstring closing quotes should be on a separate line
		"D210",  # No whitespaces allowed surrounding docstring text
		"D211",  # No blank lines allowed before class docstring
		"D212",  # Multi-line docstring summary should start at the first line
		"D213",  # Multi-line docstring summary should start at the second line
		"D214",  # Section is over-indented
		"D215",  # Section underline is over-indented
		"D300",  # Use “”“triple double quotes”“”
		"D301",  # Use r”“” if any backslashes in a docstring
		"D400",  # First line should end with a period
		# "D401",  # First line should be in imperative mood
		"D402",  # First line should not be the function’s "signature"
		"D403",  # First word of the first line should be properly capitalized
		"D404",  # First word of the docstring should not be "This"
		"D415",  # First line should end with a period, question mark, or exclamation point
		"D417",  # Missing argument descriptions in the docstring
		]

# flake8_slots
code_only_warning.extend((
		"SLOT000",  # Define __slots__ for subclasses of str
		"SLOT001",  # Define __slots__ for subclasses of tuple
		"SLOT002",  # Define __slots__ for subclasses of collections.namedtuple
		))

# flake8-pyi
lint_warn_list.extend([
		"Y001,"  # Names of TypeVars in stubs should start with _.
		"Y002",  # If test must be a simple comparison against sys.platform or sys.version_info.
		"Y003",  # Unrecognized sys.version_info check.
		"Y004",  # Version comparison must use only major and minor version.
		"Y005",  # Version comparison must be against a length-n tuple.
		"Y006",  # Use only < and >= for version comparisons.
		"Y007",  # Unrecognized sys.platform check. Platform checks should be simple string comparisons.
		"Y008",  # Unrecognized platform.
		"Y009",  # Empty body should contain "...", not "pass".
		"Y010",  # Function body must contain only "...".
		"Y011",  # All default values for typed function arguments must be "...".
		"Y012",  # Class body must not contain "pass".
		"Y013",  # Non-empty class body must not contain "...".
		"Y014",  # All default values for arguments must be "...".
		"Y015",  # Attribute must not have a default value other than "...".
		"Y090",  # Use explicit attributes instead of assignments in __init__.
		"Y091",  # Function body must not contain "raise".
		])

# flake8-noqa
lint_warn_list.extend([
		"NQA001",  # "  #noqa  " must have a single space after the hash, e.g. "# noqa
		"NQA002",  # "  # noqa X000  " must have a colon, e.g. "# noqa: X000
		"NQA003",  # "  # noqa : X000  " must not have a space before the colon, e.g. "# noqa: X000"
		"NQA004",  # "  # noqa: X000  " must have at most one space before the codes, e.g. "# noqa: X000
		"NQA005",  # "  # noqa: X000,X000  " has duplicate codes, remove X00
		"NQA102",  # "  # noqa: X000  " has no matching violation
		"NQA103",  # "  # noqa: X000,X001  " has unmatched code(s), remove X00
		])


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
