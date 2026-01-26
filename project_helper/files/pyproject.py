#!/usr/bin/env python
#
#  packaging.py
"""
Manage configuration files for packaging tools.
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
from typing import Any, List

# 3rd party
import dom_toml
from domdf_python_tools.paths import PathPlus
from repo_helper.files.packaging import DefaultDict
from repo_helper.templates import Environment

# this package
from project_helper.files import management

__all__ = ["make_pyproject"]


@management.register("pyproject")
def make_pyproject(project: pathlib.Path, templates: Environment) -> List[str]:
	"""
	Create the ``pyproject.toml`` file for :pep:`517`.

	:param project: Path to the project root.
	:param templates:
	"""

	pyproject_file = PathPlus(project / "pyproject.toml")

	data: DefaultDict[str, Any]

	if pyproject_file.is_file():
		data = DefaultDict(dom_toml.load(pyproject_file))
	else:
		data = DefaultDict()

	# tool
	data.set_default("tool", {})

	# TODO
	# if not templates.globals["enable_tests"] and not templates.globals["stubs_package"]:
	# 	data["tool"]["importcheck"] = data["tool"].get("importcheck", {})

	# [tool.mypy]
	data["tool"].setdefault("mypy", {})
	data["tool"]["mypy"]["python_version"] = "3.6"
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
