#!/usr/bin/env python
#
#  __init__.py
"""
Functions to create files.
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
import inspect
import pathlib
from typing import Any, Callable, List, Optional, Sequence, Tuple

# 3rd party
import jinja2
from domdf_python_tools.bases import UserList

# this package
from project_helper.templates import Environment

jinja2.Environment.__module__ = "jinja2"

__all__ = ["Management", "management", "is_registered", "Manager"]

#: Type hint for a function that manages files.
Manager = Callable[[pathlib.Path, Environment], List[str]]


class Management(UserList[Tuple[Manager, str, Sequence[str]]]):
	"""
	Class to store functions that manage files.

	The syntax of each entry is:

	* the function,
	* a string to use in ``exclude_files`` to disable this function,
	* a list of strings representing config values that must be true to call the function.
	"""

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

	def register(
			self,
			exclude_name: str,
			exclude_unless_true: Sequence[str] = (),
			*,
			name: Optional[str] = None,
			) -> Callable:
		"""
		Decorator to register a function.

		The function must have the following signature:

		.. code-block:: python

			def function(
				project: pathlib.Path,
				templates: jinja2.Environment,
				) -> List[str]: ...

		:param exclude_name: A string to use in 'exclude_files' to disable this function.
		:param exclude_unless_true: A list of strings representing config values that must be true to call the function.
		:param name: Optional name to use for the function in the output. Defaults to the name of the function.
		:no-default name:

		:return: The registered function.

		:raises: :exc:`SyntaxError` if the decorated function does not take the correct arguments.
		"""

		def _decorator(function: Callable) -> Callable:
			signature = inspect.signature(function)

			if list(signature.parameters.keys()) != ["project", "templates"]:
				raise SyntaxError(
						"The decorated function must take only the following arguments: 'project' and 'templates'",
						)

			self.append((function, exclude_name, exclude_unless_true))

			if name:
				function.__name__ = name

			setattr(function, "_repo_helper_registered", True)

			return function

		return _decorator


management = Management()


def is_registered(obj: Any) -> bool:
	"""
	Return whether ``obj`` is a registered function.

	:param obj:

	.. TODO:: Allow all callables
	"""

	if inspect.isfunction(obj):
		return bool(getattr(obj, "_repo_helper_registered", False))

	return False
