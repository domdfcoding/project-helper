#!/usr/bin/env python
#
#  __init__.py
"""
Core CLI tools.

.. note::

	Enable autocompletion with:

	.. prompt:: bash

		_REPO_HELPER_COMPLETE=source_bash repo-helper > /usr/share/bash-completion/completions/repo-helper

		_REPO_HELPER_COMPLETE=source_bash repo-helper | sudo tee /usr/share/bash-completion/completions/repo-helper


	.. seealso:: https://click.palletsprojects.com/en/7.x/bashcomplete/#activation
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
import sys
from functools import partial
from typing import Optional

# 3rd party
import click
from click import Context
from consolekit import CONTEXT_SETTINGS, SuggestionGroup, click_group
from consolekit.options import force_option
from domdf_python_tools.paths import PathPlus
from southwark.click import commit_message_option, commit_option

# this package
from repo_helper import __version__
from repo_helper.cli.utils import run_repo_helper

__all__ = ["cli", "cli_command", "cli_group"]


@click.version_option(__version__)
@click_group(invoke_without_command=True)
@force_option(help_text="Run 'repo_helper' even when the git working directory is not clean.")
@commit_option(default=None)
@commit_message_option("Updated files with 'repo_helper'.")
@click.pass_context
def cli(ctx: Context, force: bool, commit: Optional[bool], message: str):
	"""
	Update files in the given repositories, based on settings in 'repo_helper.yml'.
	"""

	path = PathPlus.cwd()
	ctx.obj["PATH"] = path
	ctx.obj["commit"] = commit
	ctx.obj["force"] = force

	if ctx.invoked_subcommand is None:
		sys.exit(run_repo_helper(path=path, force=force, initialise=False, commit=commit, message=message))

	else:
		if message != "Updated files with 'repo_helper'.":
			raise click.UsageError(
					f"--message cannot be used before a command. "
					f"Perhaps you meant 'repo_helper {ctx.invoked_subcommand} --message'?"
					)


cli_command = partial(cli.command, context_settings=CONTEXT_SETTINGS)
cli_group = partial(cli.group, context_settings=CONTEXT_SETTINGS, cls=SuggestionGroup)
