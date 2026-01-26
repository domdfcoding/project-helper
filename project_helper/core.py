#!/usr/bin/env python
#
#  core.py
"""
Core functionality of ``project_helper``.
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
import os.path
from typing import List, Tuple, Type

# 3rd party
import jinja2
from domdf_python_tools.import_tools import discover
from domdf_python_tools.paths import PathPlus, traverse_to_file
from domdf_python_tools.typing import PathLike
from repo_helper.utils import brace, discover_entry_points

# this package
import project_helper.files
from project_helper.configuration import parse_yaml
from project_helper.files import Management, is_registered, management
from project_helper.files.qa import make_formate_toml
from project_helper.templates import Environment, template_dir

__all__ = [
		"ProjectHelper",
		"import_registered_functions",
		]


def import_registered_functions() -> List[Type]:
	"""
	Returns a list of all registered functions.
	"""

	local_functions = discover(project_helper.files, is_registered)
	third_party_commands = discover_entry_points("repo_helper.command", is_registered)
	return [*local_functions, *third_party_commands]


class ProjectHelper:
	"""
	Project Helper: Manage configuration files with ease.

	:param target_repo: The path to the root of the repository to manage files for.
	:param managed_message: Message placed at the top of files to indicate that they are managed by ``repo_helper``.
	"""

	#: The target repository
	target_repo: PathPlus

	#: Provides the templates and stores the configuration.
	templates: Environment

	#: List of functions to manage files.
	files: Management

	def __init__(
			self,
			target_repo: PathLike,
			managed_message="This file is managed by 'project_helper'. Don't edit it directly."
			):
		import_registered_functions()

		# Walk up the tree until a "repo_helper.yml" or "git_helper.yml" (old name) file is found.
		self.target_repo = traverse_to_file(PathPlus(target_repo), "project_helper.yml")

		self.templates = Environment(
				loader=jinja2.FileSystemLoader(str(template_dir)),
				undefined=jinja2.StrictUndefined,
				)
		self.templates.globals["managed_message"] = managed_message
		self.templates.globals["brace"] = brace

		# formate.toml must always run last
		self.files = management + [(make_formate_toml, "formate", [])]

	@property
	def managed_message(self) -> str:
		"""
		Message placed at the top of files to indicate that they are managed by ``repo_helper``.
		"""

		return self.templates.globals["managed_message"]

	@managed_message.setter
	def managed_message(self, value: str) -> None:
		"""
		Message placed at the top of files to indicate that they are managed by ``repo_helper``.
		"""

		self.templates.globals["managed_message"] = str(value)

	def load_settings(self, allow_unknown_keys: bool = False) -> None:
		"""
		Load settings from the ``repo_helper.yml`` file in the repository.

		:param allow_unknown_keys: Whether unknown keys should be allowed in the configuration file.
		"""

		config_vars = parse_yaml(self.target_repo, allow_unknown_keys=allow_unknown_keys)
		self.templates.globals.update(config_vars)
		self.templates.globals["len"] = len
		self.templates.globals["join_path"] = os.path.join

	@property
	def exclude_files(self) -> Tuple[str, ...]:
		"""
		A tuple of excluded files that should **NOT** be managed by ``project_helper``.
		"""

		return tuple(self.templates.globals["exclude_files"])

	def run(self) -> List[str]:
		"""
		Run ``project_helper`` for the repository and update all managed files.

		:return: A list of files managed by ``project_helper``,
			regardless of whether they were added, removed or modified.
		"""

		all_managed_files = []

		for function_, exclude_name, other_requirements in self.files:
			if exclude_name not in self.exclude_files and all([
					self.templates.globals[req] for req in other_requirements
					]):

				output_filenames = function_(self.target_repo, self.templates)

				for filename in output_filenames:
					all_managed_files.append(str(filename))

		all_managed_files.append("project_helper.yml")

		return sorted(set(all_managed_files))
