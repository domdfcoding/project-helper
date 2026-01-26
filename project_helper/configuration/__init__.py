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
import itertools
import json
import re
from typing import Any, Dict, List

# 3rd party
import click
from configconfig.metaclass import ConfigVarMeta
from configconfig.parser import Parser
from configconfig.utils import make_schema
from domdf_python_tools.compat import importlib_resources
from domdf_python_tools.paths import PathPlus
from domdf_python_tools.stringlist import StringList
from domdf_python_tools.typing import PathLike

# this package
from repo_helper.configuration.metadata import (
		assignee,
		author,
		copyright_years,
		email,
		license,
		name,
		repo_name,
		source_files,
		username
		)
from repo_helper.configuration.other import additional_ignore, exclude_files, imgbot_ignore
from repo_helper.configuration.qa import (
		enable_pre_commit,
		mypy_deps,
		mypy_plugins,
		mypy_version,
		pre_commit_exclude,
		tox_unmanaged,
		yapf_exclude
		)

__all__ = [
		"RepoHelperParser",
		"dump_schema",
		"name",
		"author",
		"email",
		"username",
		"repo_name",
		"copyright_years",
		"license",
		"assignee",
		"source_files",
		"additional_ignore",
		"exclude_files",
		"imgbot_ignore",
		"mypy_deps",
		"mypy_plugins",
		"mypy_version",
		"tox_unmanaged",
		"yapf_exclude",
		"enable_pre_commit",
		"pre_commit_exclude",
		]

_REMOVED_KEYS_RE = re.compile("^(use_travis|travis_pypi_secure|travis_site|use_experimental_backend)")


def parse_yaml(repo_path: PathLike, allow_unknown_keys: bool = False) -> Dict:
	"""
	Parse configuration values from ``repo_helper.yml``.

	:param repo_path: Path to the repository root.
	:param allow_unknown_keys: Whether unknown keys should be allowed in the configuration file.

	:returns: Mapping of configuration keys to values.

	.. versionchanged:: 2021.2.18  Added the ``allow_unknown_keys`` argument.
	"""

	repo_path = PathPlus(repo_path)

	if (repo_path / "git_helper.yml").is_file():
		(repo_path / "git_helper.yml").rename(repo_path / "repo_helper.yml")

	config_file = repo_path / "repo_helper.yml"

	if not config_file.is_file():
		raise FileNotFoundError(f"'repo_helper.yml' not found in {repo_path}")

	content_lines = config_file.read_lines()

	lines_without_removed_keys = StringList(
			itertools.filterfalse(
					_REMOVED_KEYS_RE.match,  # type: ignore
					content_lines,
					),
			)
	lines_without_removed_keys.blankline(ensure_single=True)

	if lines_without_removed_keys != content_lines:
		config_file.write_lines(lines_without_removed_keys)

	parser = RepoHelperParser(allow_unknown_keys=allow_unknown_keys)
	return parser.run(config_file)


all_values: List[ConfigVarMeta] = []

for module in [
		metadata,
		other,
		qa,
		]:

	for item in module.__all__:  # type: ignore
		confvar = getattr(module, item)
		if isinstance(confvar, ConfigVarMeta):
			all_values.append(confvar)

all_values.sort(key=lambda v: v.__name__)


class RepoHelperParser(Parser):
	"""
	Parses the configuration fron ``repo_helper.yml``.
	"""

	config_vars: List[ConfigVarMeta] = all_values


def dump_schema() -> Dict[str, Any]:
	"""
	Dump the schema for ``repo_helper.yml`` to ``repo_helper/repo_helper_schema.json``
	and return the schema as a dictionary.
	"""  # noqa: D400

	schema = make_schema(*all_values)

	with importlib_resources.path(project_helper, "project_helper_schema.json") as schema_file:
		PathPlus(schema_file).write_clean(json.dumps(schema, indent=2))
		click.echo(f"Wrote schema to {schema_file}")

	return schema
