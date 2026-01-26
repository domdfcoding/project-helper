#!/usr/bin/env python
#
#  __init__.py
"""
Core CLI tools.

.. note::

	Enable autocompletion with:

	.. prompt:: bash

		_PROJECT_HELPER_COMPLETE=source_bash repo-helper > /usr/share/bash-completion/completions/repo-helper

		_PROJECT_HELPER_COMPLETE=source_bash repo-helper | sudo tee /usr/share/bash-completion/completions/repo-helper


	.. seealso:: https://click.palletsprojects.com/en/7.x/bashcomplete/#activation
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
import sys
from contextlib import suppress
from functools import partial

# 3rd party
import click
from click import Context
from consolekit import CONTEXT_SETTINGS, SuggestionGroup, click_group
from consolekit.utils import abort
from domdf_python_tools.paths import PathPlus
from dulwich.errors import NotGitRepository
from repo_helper.utils import stage_changes

# this package
from project_helper import __version__

__all__ = ["cli", "cli_command", "cli_group"]


@click.version_option(__version__)
@click_group(invoke_without_command=True)
@click.pass_context
def cli(ctx: Context) -> None:  # noqa: PRM002
	"""
	Update files in the project, based on settings in 'project_helper.yml'.
	"""

	# stdlib
	import textwrap

	# 3rd party
	from repo_helper.utils import easter_egg

	# this package
	from project_helper.core import ProjectHelper

	path = PathPlus.cwd()
	ctx.obj["PATH"] = path

	if ctx.invoked_subcommand is None:

		try:
			rh = ProjectHelper(path)
			rh.load_settings()
		except FileNotFoundError as e:
			error_block = textwrap.indent(str(e), '\t')
			raise abort(f"Unable to run 'project_helper'.\nThe error was:\n{error_block}")

		managed_files = rh.run()

		print("Success!")
		easter_egg()

		with suppress(NotGitRepository):
			stage_changes(rh.target_repo, managed_files)
			click.echo("\nChanged files were staged for commit with git.")
			click.echo('  (use "git status" to view staged changes')
			click.echo('   and "git rm --cached <file>..." to unstage)')

		sys.exit(0)


cli_command = partial(cli.command, context_settings=CONTEXT_SETTINGS)
cli_group = partial(cli.group, context_settings=CONTEXT_SETTINGS, cls=SuggestionGroup)
