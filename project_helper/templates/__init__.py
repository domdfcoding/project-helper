#!/usr/bin/env python
#
#  templates.py
"""
Contains the :class:`pathlib.Path` objects representing the templates directory (:data:`template_dir`),
and the directory representing the files used to initialise a new repository (:data:`init_repo_template_dir`).
"""  # noqa: D400
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
from typing import Any, Dict

# 3rd party
import jinja2
from domdf_python_tools.paths import PathPlus

__all__ = ["template_dir", "init_repo_template_dir"]

#: The templates directory.
template_dir = PathPlus(__file__).parent.absolute()

#: The directory representing the files used to initialise a new repository
init_repo_template_dir = (PathPlus(__file__).parent / "init_repo_files").absolute()


class Environment(jinja2.Environment):
	globals: Dict[str, Any]  # noqa: A003  # pylint: disable=redefined-builtin


Environment.__module__ = jinja2.Environment.__module__
Environment.__qualname__ = jinja2.Environment.__qualname__
