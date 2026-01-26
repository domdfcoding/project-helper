#!/usr/bin/env python
#
#  wizard.py
"""
Wizard 🧙‍ for creating a 'project_helper.yml' file.
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
import os
from contextlib import suppress
from typing import Any, Dict

# 3rd party
import click
from domdf_python_tools.paths import PathPlus
from dulwich.errors import NotGitRepository
from southwark.repo import Repo
from repo_helper.utils import _round_trip_dump, easter_egg, license_lookup, stage_changes
from repo_helper.utils import get_license_text

# this package
from project_helper.cli import cli_command



__all__ = ["wizard"]


@cli_command()
def wizard() -> None:
	"""
	Run the wizard 🧙 to initialize the project and  create a 'project_helper.yml' file.
	"""

	# stdlib
	import datetime
	import textwrap

	# 3rd party
	from apeye.email_validator import EmailSyntaxError, validate_email
	from consolekit.input import confirm, prompt
	from consolekit.utils import abort
	from ruamel.yaml import scalarstring

	# this package
	from project_helper.core import ProjectHelper

	path = PathPlus.cwd()
	config_file = path / "project_helper.yml"

	# ---------- intro ----------
	click.echo("This wizard 🧙‍ will guide you through initializing your project.")

	# ---------- file exists warning ----------
	if config_file.is_file():
		click.echo(f"\nWoah! A 'project_helper.yml' file already exists. It will be overwritten if you continue!")
		if not confirm("Are you sure you want to continue?"):
			raise click.Abort()

	click.echo("\nDefault options are indicated in [square brackets].")
	data: Dict[str, Any] = {}

	# ---------- name ----------
	click.echo("\nThe name of the library/project.")
	name = prompt("Name", default=path.name)

	# ---------- author ----------
	click.echo("\nThe name of the author (you).")

	author = prompt("Name", default=get_default_author(path))
	data["author"] = scalarstring.SingleQuotedScalarString(author)

	# ---------- email ----------

	click.echo("\nThe email address of the author.")

	while True:
		try:
			email = validate_email(prompt("Email", default=get_default_email(path, author))).email
			break
		except EmailSyntaxError:
			click.echo("That is not a valid email address.")

	data["email"] = scalarstring.SingleQuotedScalarString(email)

	# ---------- GitHub ----------
	on_github = confirm("\nWill this project be hosted on GitHub?", default=True)

	if on_github:
		data["on_github"] = True

		# ---------- username ----------
		username = prompt("The username of the author on GitHub.", default=author)
		data["username"] = data["assignee"] = scalarstring.SingleQuotedScalarString(username)

		# ---------- repo_name ----------
		repo_name = prompt("The repository name on GitHub.", default=name)
		data["repo_name"] = scalarstring.SingleQuotedScalarString(repo_name)

	# ---------- copyright_years ----------
	click.echo("\nThe copyright years for the library.")
	copyright_years = prompt("Copyright years", default=str(datetime.datetime.today().year), type=str)

	# ---------- license_ ----------
	click.echo(
			"""
The SPDX identifier for the license this library is distributed under.
Not all SPDX identifiers are supported."""
			)

	while True:
		license_ = prompt("License")

		if license_ in license_lookup:
			break
		else:
			click.echo("That is not a supported identifier.")

	# ---------- source_files ----------

	click.echo("\nType in the paths to the source files that are part of this project.")
	click.echo("Press 'enter' on a blank line to finish.")

	source_files = []

	while True:
		# TODO: tab completion
		path = prompt("> ", default='', prompt_suffix='', show_default=False)
		if path:
			source_files.append(path)
		else:
			click.echo()
			break

	data["source_files"] = source_files

	# ---------- writeout ----------

	config_file.write_lines(["---", _round_trip_dump(data)])

	# ---------- initialize ----------

	try:
		rh = ProjectHelper(path)
		rh.load_settings()
	except FileNotFoundError as e:
		error_block = textwrap.indent(str(e), '\t')
		raise abort(f"Unable to run 'project_helper'.\nThe error was:\n{error_block}")

	# r = Repo(rh.target_repo)

	rh.templates.globals["len"] = len
	rh.templates.globals["license"] = license_
	rh.templates.globals["copyright_years"] = copyright_years

	to_stage = ["requirements.txt", "LICENSE", "README.rst"]

	# Create README.rst
	template = rh.templates.get_template("README.rst")
	(rh.target_repo / "README.rst").write_clean(template.render(name=name))

	# Create LICENSE
	(rh.target_repo / "LICENSE").write_clean(get_license_text(
			license_,
			copyright_years,
			author,
			name,
			))

	# Touch requirements.txt
	(rh.target_repo / "requirements.txt").touch()

	to_stage.extend(rh.run())

	click.echo(
			f"""
The options you provided have been written to the file {config_file}.
You can configure additional options in that file.

project_helper can now be run with the 'project_helper' command in the project root.
"""
			)

	with suppress(NotGitRepository):
		stage_changes(rh.target_repo, to_stage)
		click.echo("\nNewly created files were staged for commit with git.")
		click.echo('  (use "git status" to view staged changes')
		click.echo('   and "git rm --cached <file>..." to unstage)')

	click.echo("\nBe seeing you!")
	easter_egg()


def get_default_author(path: PathPlus) -> str:

	# stdlib
	import getpass

	# Fallback values
	try:
		default_author = getpass.getuser()
	except ImportError:
		# Usually USERNAME is not set when trying getpass.getuser()
		default_author = ''

	# Use git environment variables if available.
	default_author = os.environ.get("GIT_COMMITTER_NAME", default=default_author)
	default_author = os.environ.get("GIT_AUTHOR_NAME", default=default_author)

	# Get git config if a git repository. Don't if can't
	with suppress(NotGitRepository):
		r = Repo(path)
		git_config = r.get_config_stack()

		with suppress(KeyError):
			default_author = git_config.get(("user", ), "name").decode("UTF-8")

	return default_author


def get_default_email(path: PathPlus, author: str) -> str:

	# stdlib
	import socket

	# Fallback value
	default_email = f"{author}@{socket.gethostname()}"

	# Use git environment variables if available.
	default_email = os.environ.get("GIT_COMMITTER_EMAIL", default=default_email)
	default_email = os.environ.get("GIT_AUTHOR_EMAIL", default=default_email)

	# Get git config if a git repository. Don't if can't
	with suppress(NotGitRepository):
		r = Repo(path)
		git_config = r.get_config_stack()

		with suppress(KeyError):
			default_email = git_config.get(("user", ), "email").decode("UTF-8")

	return default_email
