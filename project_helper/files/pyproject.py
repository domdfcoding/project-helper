#!/usr/bin/env python
#
#  packaging.py
"""
Manage configuration files for packaging tools.
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
import copy
import pathlib
import posixpath
import re
import textwrap
from typing import Any, Dict, List, Mapping, Tuple, TypeVar

# 3rd party
import dom_toml
from domdf_python_tools.compat import importlib_resources
from domdf_python_tools.paths import PathPlus
from natsort import natsorted
from shippinglabel import normalize
from shippinglabel.requirements import ComparableRequirement, combine_requirements

# this package
import repo_helper.files
from repo_helper.configupdater2 import ConfigUpdater
from repo_helper.configuration import _pypy_version_re
from repo_helper.files import management
from repo_helper.templates import Environment
from repo_helper.utils import IniConfigurator, indent_join, indent_with_tab, license_lookup

__all__ = ["make_pyproject"]

_KT = TypeVar("_KT")
_VT_co = TypeVar("_VT_co")


class DefaultDict(Dict[_KT, _VT_co]):

	__slots__ = ["__defaults"]

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.__defaults = {}

	def set_default(self, key: _KT, default: _VT_co) -> None:
		self.__defaults[key] = default

	def __getitem__(self, item) -> _VT_co:
		if item not in self and item in self.__defaults:
			self[item] = self.__defaults[item]

		return super().__getitem__(item)


pre_release_re = re.compile(".*(-dev|alpha|beta)", re.IGNORECASE)


@management.register("pyproject")
def make_pyproject(repo_path: pathlib.Path, templates: Environment) -> List[str]:
	"""
	Create the ``pyproject.toml`` file for :pep:`517`.

	:param repo_path: Path to the repository root.
	:param templates:
	"""

	pyproject_file = PathPlus(repo_path / "pyproject.toml")

	data: DefaultDict[str, Any]

	if pyproject_file.is_file():
		data = DefaultDict(dom_toml.load(pyproject_file))
	else:
		data = DefaultDict()

	# tool
	data.set_default("tool", {})

	# tool.mkrecipe
	if templates.globals["enable_conda"]:
		data["tool"].setdefault("mkrecipe", {})
		data["tool"]["mkrecipe"]["conda-channels"] = templates.globals["conda_channels"]

		if templates.globals["conda_extras"] in (["none"], ["all"]):
			data["tool"]["mkrecipe"]["extras"] = templates.globals["conda_extras"][0]
		else:
			data["tool"]["mkrecipe"]["extras"] = templates.globals["conda_extras"]
	else:
		if "mkrecipe" in data["tool"]:
			del data["tool"]["mkrecipe"]

	# tool.whey
	data["tool"].setdefault("whey", {})

	data["tool"]["whey"]["base-classifiers"] = templates.globals["classifiers"]

	python_versions = set()
	python_implementations = set()

	for py_version in templates.globals["python_versions"]:
		py_version = str(py_version)

		if pre_release_re.match(py_version):
			continue

		pypy_version_m = _pypy_version_re.match(py_version)

		if py_version.startswith('3'):
			python_versions.add(py_version)
			python_implementations.add("CPython")

		elif pypy_version_m:
			python_implementations.add("PyPy")
			python_versions.add(f"3.{pypy_version_m.group(1)}")

	license_ = templates.globals["license"]
	data["tool"]["whey"]["license-key"] = {v: k for k, v in license_lookup.items()}.get(license_, license_)

	if templates.globals["import_name"] != templates.globals["modname"]:
		data["tool"]["whey"]["package"] = posixpath.join(
				# templates.globals["source_dir"],
				templates.globals["import_name"].split('.', 1)[0],
				)

	if templates.globals["manifest_additional"]:
		data["tool"]["whey"]["additional-files"] = templates.globals["manifest_additional"]
	elif "additional-files" in data["tool"]["whey"]:
		del data["tool"]["whey"]["additional-files"]

	# TODO
	# if not templates.globals["enable_tests"] and not templates.globals["stubs_package"]:
	# 	data["tool"]["importcheck"] = data["tool"].get("importcheck", {})

	# [tool.mypy]
	data["tool"].setdefault("mypy", {})
	data["tool"]["mypy"]["python_version"] = templates.globals["min_py_version"]
	data["tool"]["mypy"]["namespace_packages"] = True
	data["tool"]["mypy"]["check_untyped_defs"] = True
	data["tool"]["mypy"]["warn_unused_ignores"] = True
	data["tool"]["mypy"]["no_implicit_optional"] = True
	data["tool"]["mypy"]["show_error_codes"] = True

	if templates.globals["mypy_plugins"]:
		data["tool"]["mypy"]["plugins"] = templates.globals["mypy_plugins"]

	if not data["tool"]:
		del data["tool"]

	# TODO: managed message
	dom_toml.dump(data, pyproject_file, encoder=dom_toml.TomlEncoder)

	return [pyproject_file.name]
