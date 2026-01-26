#!/usr/bin/env python
#
#  configuration.py
"""
Configuration options.
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
import json
from operator import attrgetter
from typing import Any, Dict, List, MutableMapping

# 3rd party
import click
from configconfig.metaclass import ConfigVarMeta
from configconfig.parser import Parser
from configconfig.utils import make_schema
from domdf_python_tools.compat import importlib_resources
from domdf_python_tools.paths import PathPlus
from domdf_python_tools.typing import PathLike

# this package
from project_helper.configuration import metadata, other, qa

# from project_helper.configuration.metadata import assignee, author, email, name, repo_name, source_files, username
# from project_helper.configuration.other import additional_ignore, exclude_files, imgbot_ignore, on_github
# from project_helper.configuration.qa import (
# 		mypy_deps,
# 		mypy_plugins,
# 		mypy_version,
# 		pre_commit_exclude,
# 		tox_unmanaged,
# 		yapf_exclude
# 		)

__all__ = ["ProjectHelperParser", "dump_schema", "parse_yaml"]


def parse_yaml(project: PathLike, allow_unknown_keys: bool = False) -> MutableMapping:
	"""
	Parse configuration values from ``project_helper.yml``.

	:param project: Path to the project root.
	:param allow_unknown_keys: Whether unknown keys should be allowed in the configuration file.

	:returns: Mapping of configuration keys to values.
	"""

	project = PathPlus(project)
	config_file = project / "project_helper.yml"

	if not config_file.is_file():
		raise FileNotFoundError(f"'project_helper.yml' not found in {project}")

	parser = ProjectHelperParser(allow_unknown_keys=allow_unknown_keys)
	return parser.run(config_file)


all_values: List[ConfigVarMeta] = []

for module in [metadata, other, qa]:

	for item in module.__all__:
		confvar = getattr(module, item)
		if isinstance(confvar, ConfigVarMeta):
			all_values.append(confvar)

all_values.sort(key=attrgetter("__name__"))


class ProjectHelperParser(Parser):
	"""
	Parses the configuration from ``project_helper.yml``.
	"""

	config_vars: List[ConfigVarMeta] = all_values


def dump_schema() -> Dict[str, Any]:
	"""
	Dump the schema for ``project_helper.yml`` to ``project_helper/project_helper_schema.json``.

	:returns: The schema as a dictionary.
	"""

	schema = make_schema(*all_values)

	with importlib_resources.path("project_helper", "project_helper_schema.json") as schema_file:
		PathPlus(schema_file).write_clean(json.dumps(schema, indent=2))
		click.echo(f"Wrote schema to {schema_file}")

	return schema
