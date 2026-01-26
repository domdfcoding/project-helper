#!/usr/bin/env python
#
#  testing.py
r"""
:class:`~configconfig.configvar.ConfigVar`\s in the "testing" category.
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
import re
from typing import Any, Dict, List, Optional, Union

# 3rd party
from configconfig.configvar import ConfigVar

__all__ = [
		"mypy_deps",
		"mypy_plugins",
		"mypy_version",
		"tox_unmanaged",
		"yapf_exclude",
		"enable_pre_commit",
		"pre_commit_exclude",
		]


class mypy_deps(ConfigVar):  # noqa
	"""
	A list of additional packages to install in Tox when running mypy. Usually type stubs.

	.. code-block:: yaml

		mypy_deps:
		  - docutils-stubs
		  - webcolors-stubs
		  - gi-stubs
	"""

	dtype = List[str]
	default: List[str] = []
	category: str = "testing"


class mypy_plugins(ConfigVar):  # noqa
	"""
	A list of plugins to enable for mypy.

	Example:

	.. code-block:: yaml

		mypy_plugins:
		  - /one/plugin.py
		  - other.plugin
		  - custom_plugin:custom_entry_point

	See https://mypy.readthedocs.io/en/stable/extending_mypy.html#extending-mypy-using-plugins for more info.
	"""

	dtype = List[str]
	default: List[str] = []
	category: str = "testing"


class mypy_version(ConfigVar):  # noqa
	"""
	The version of ``mypy`` to use.

	Example:

	.. code-block:: yaml

		mypy_version: 0.920
	"""

	dtype = Union[str, float]
	rtype = str
	default = "0.910"
	category: str = "testing"


class tox_unmanaged(ConfigVar):  # noqa
	"""
	A list of section names in ``tox.ini`` which should not be managed by ``project-helper``.

	Example:

	.. code-block:: yaml

		tox_unmanaged:
		  - "testenv"
		  - "flake8"
	"""

	dtype = List[str]
	default: List[str] = []
	category: str = "testing"


class yapf_exclude(ConfigVar):  # noqa
	"""
	A list of regular expressions to use to exclude files and directories from autoformatting.

	Example:

	.. code-block:: yaml

		yapf_exclude:
		  - ".*/templates/.*"
	"""

	dtype = List[str]
	default: List[str] = []


class enable_pre_commit(ConfigVar):  # noqa
	"""
	Whether pre-commit should be installed and configured.

	Example:

	.. code-block:: yaml

		enable_pre_commit: True
	"""

	dtype = bool
	default = True
	category: str = "other"


class pre_commit_exclude(ConfigVar):  # noqa
	r"""
	Regular expression for files that should not be checked by pre_commit.

	.. code-block:: yaml

		pre_commit_exclude: "^.*\\._py$"
	"""

	dtype = str
	default: str = "^$"

	@classmethod
	def validate(cls, raw_config_vars: Optional[Dict[str, Any]] = None) -> Any:  # noqa: D102
		return re.compile(super().validate(raw_config_vars)).pattern
