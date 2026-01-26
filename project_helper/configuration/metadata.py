#!/usr/bin/env python
#
#  metadata.py
r"""
:class:`~configconfig.configvar.ConfigVar`\s in the "metadata" category.
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
from typing import List, Union

# 3rd party
from configconfig.configvar import ConfigVar

# this package
from repo_helper.utils import license_lookup

__all__ = [
		"name",
		"author",
		"email",
		"username",
		"repo_name",
		"copyright_years",
		"license",
		"assignee",
		"source_files",
		]


class name(ConfigVar):  # noqa
	"""
	The name of the project.
	"""

	dtype = str
	required = True
	category: str = "metadata"


class author(ConfigVar):  # noqa
	"""
	The name of the package author.

	Example:

	.. code-block:: yaml

		author: Dominic Davis-Foster
	"""

	dtype = str
	required = True
	category: str = "metadata"


class email(ConfigVar):  # noqa
	"""
	The email address of the author or maintainer.

	Example:

	.. code-block:: yaml

		email: dominic@example.com
	"""

	dtype = str
	required = True
	category: str = "metadata"


class username(ConfigVar):  # noqa
	"""
	The username of the GitHub account hosting the repository.

	Example:

	.. code-block:: yaml

		username: domdfcoding
	"""

	dtype = str
	default = ''
	category: str = "metadata"


class repo_name(ConfigVar):  # noqa
	"""
	The name of GitHub repository.
	"""

	dtype = str
	default = ''
	category: str = "metadata"


class assignee(ConfigVar):  # noqa
	"""
	The username of the GitHub account to assign issues to.

	Defaults to :conf:`username` if unset.

	Example:

	.. code-block:: yaml

		username: repo-helper
		assignee: domdfcoding

	.. versionadded:: 2020.11.23
	"""

	dtype = str
	default = username
	category: str = "metadata"


class copyright_years(ConfigVar):  # noqa
	"""
	The copyright_years of the package.

	Examples:

	.. code-block:: yaml

		version: 2020

	or

	.. code-block:: yaml

		version: 2014-2019
	"""

	dtype = Union[str, int]
	rtype = str
	required = True
	category: str = "metadata"


class license(ConfigVar):  # noqa  # pylint: disable=redefined-builtin
	"""
	The license for the project.

	Example:

	.. code-block:: yaml

		license: GPLv3+

	Currently understands ``LGPLv3``, ``LGPLv3``, ``GPLv3``, ``GPLv3``, ``GPLv2`` and ``BSD``.
	"""

	dtype = str
	required = True
	category: str = "metadata"

	@classmethod
	def validator(cls, value):  # noqa: D102
		value = value.replace(' ', '')

		if value in license_lookup:
			value = license_lookup[value]

		return value


class source_files(ConfigVar):  # noqa
	"""
	List of source files belonging to the project, relative to the repository root..
	"""

	dtype = List[str]
	default = []
	category: str = "metadata"
