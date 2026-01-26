#!/usr/bin/env python
#
#  pre_commit.py
"""
Configuration for `pre-commit <https://pre-commit.com>`_.
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
import re
from io import StringIO
from textwrap import indent
from typing import List

# 3rd party
import ruamel.yaml
from domdf_python_tools.paths import PathPlus
from domdf_python_tools.stringlist import StringList
from repo_helper.files.pre_commit import Repo, make_github_url, yaml_safe_loader
from repo_helper.templates import Environment

# this package
from project_helper.files import management

__all__ = ["make_pre_commit"]

pre_commit_hooks = Repo(
		repo=make_github_url("pre-commit", "pre-commit-hooks"),
		rev="v3.4.0",
		hooks=[
				"check-added-large-files",
				"check-ast",
				"fix-byte-order-marker",
				"check-byte-order-marker",
				"check-case-conflict",
				"check-executables-have-shebangs",
				"check-json",
				"check-toml",
				"check-yaml",
				"check-merge-conflict",
				"check-symlinks",
				"check-vcs-permalinks",
				"detect-private-key",
				"trailing-whitespace",
				"mixed-line-ending",
				"end-of-file-fixer",
				],
		)

pygrep_hooks = Repo(
		repo=make_github_url("pre-commit", "pygrep-hooks"),
		rev="v1.9.0",
		hooks=[
				"python-no-eval",
				"rst-backticks",
				"rst-directive-colons",
				"rst-inline-touching-normal",  # TODO: "python-check-blanket-type-ignore",
				],
		)

lucas_c_hooks = Repo(
		repo=make_github_url("Lucas-C", "pre-commit-hooks"),
		rev="v1.1.10",
		hooks=["remove-crlf", "forbid-crlf"],
		)

flake2lint = Repo(
		repo=make_github_url("domdfcoding", "flake2lint"),
		rev="v0.4.1",
		hooks=["flake2lint"],
		)

# shellcheck = Repo(
# 		repo=make_github_url("shellcheck-py", "shellcheck-py"),
# 		rev="v0.7.1.1",
# 		hooks=["shellcheck"]
# 		)
#
# yamllint = Repo(
# 		repo=make_github_url("adrienverge", "yamllint"),
# 		rev="v1.23.0",
# 		hooks=["yamllint"]
# 		)


@management.register("pre-commit")
def make_pre_commit(project: pathlib.Path, templates: Environment) -> List[str]:
	"""
	Add configuration for ``pre-commit``.

	https://github.com/pre-commit/pre-commit

	# See https://pre-commit.com for more information
	# See https://pre-commit.com/hooks.html for more hooks

	:param project: Path to the project root.
	:param templates:
	"""

	domdfcoding_hooks = Repo(
			repo=make_github_url("domdfcoding", "pre-commit-hooks"),
			rev="v0.2.1",
			hooks=[
					{"id": "requirements-txt-sorter", "args": ["--allow-git"]},
					{
							"id": "check-docstring-first",
							},
					"bind-requirements",
					],
			)

	yapf_exclude = templates.globals["yapf_exclude"]
	if yapf_exclude:
		formate_excludes = fr"^({'|'.join(yapf_exclude)})\.(_)?py$"
		formate_hooks = [{"id": "formate", "exclude": formate_excludes}]
	else:
		formate_hooks = ["formate"]

	formate = Repo(
			repo=make_github_url("python-formate", "formate"),
			rev="v0.4.9",
			hooks=formate_hooks,
			)

	pre_commit_file = PathPlus(project / ".pre-commit-config.yaml")

	if not pre_commit_file.is_file():
		pre_commit_file.touch()

	dumper = ruamel.yaml.YAML()
	dumper.indent(mapping=2, sequence=3, offset=1)

	output = StringList([
			f"# {templates.globals['managed_message']}",
			"---",
			'',
			f"exclude: {templates.globals['pre_commit_exclude']}",
			'',
			"repos:",
			])

	indent_re = re.compile("^ {3}")

	managed_hooks = [
			pre_commit_hooks,
			domdfcoding_hooks,
			flake2lint,
			pygrep_hooks,
			lucas_c_hooks,
			formate,
			]

	managed_hooks_urls = [str(hook.repo) for hook in managed_hooks]

	custom_hooks_comment = "# Custom hooks can be added below this comment"

	for hook in managed_hooks:
		buf = StringIO()
		dumper.dump(hook.to_dict(), buf)
		output.append(indent_re.sub(" - ", indent(buf.getvalue(), "   ")))
		output.blankline(ensure_single=True)
	output.append(custom_hooks_comment)
	output.blankline(ensure_single=True)

	raw_yaml = pre_commit_file.read_text()

	if custom_hooks_comment in raw_yaml:
		custom_hooks_yaml = pre_commit_file.read_text().split(custom_hooks_comment)[1]

		custom_hooks = []
		local_hooks = []

		for repo in yaml_safe_loader.load(custom_hooks_yaml) or []:
			if repo["repo"] == "local":
				local_hooks.append(repo)

			elif repo["repo"] not in managed_hooks_urls:
				custom_hooks.append(Repo(**repo))

		for hook in custom_hooks:
			buf = StringIO()
			dumper.dump(hook.to_dict(), buf)
			output.append(indent_re.sub(" - ", indent(buf.getvalue(), "   ")))
			output.blankline(ensure_single=True)

		for hook in local_hooks:
			buf = StringIO()
			dumper.dump(hook, buf)
			output.append(indent_re.sub(" - ", indent(buf.getvalue(), "   ")))
			output.blankline(ensure_single=True)

	pre_commit_file.write_lines(output)

	return [pre_commit_file.name]
