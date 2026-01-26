#!/usr/bin/env python
#
#  testing.py
"""
Helpers for running tests with pytest.

.. extras-require:: testing
	:pyproject:
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
import datetime
import os
import pathlib
import secrets
import sys

# 3rd party
import jinja2
import pytest  # nodep
import repo_helper
from apeye.url import URL
from dulwich.config import StackedConfig
from repo_helper.utils import brace
from southwark.repo import Repo

# this package
from project_helper.templates import Environment, template_dir

__all__ = [
		"demo_environment",
		"temp_repo",
		"temp_empty_repo",
		"example_config",
		"is_running_on_actions",
		]


@pytest.fixture()
def demo_environment() -> Environment:
	"""
	Pytest fixture to create a jinja2 environment for use in tests.

	The environment has the following variables available by default:

	.. code-block:: python

		{
			"author": "Bob & Alice",
			"email": "bob@example.com",
			"username": "octocat",
			"repo_name": "circuitpython_hello_world",
			"assignee": "octocat",
			"source_files": ["code.py", "boot.py", "secrets.py"],
			"additional_ignore": ["foo", "bar", "fuzz"],
			"imgbot_ignore": ["**/*.svg"],
			"exclude_files": [],
			"on_github": True,
			"mypy_deps": [],
			"mypy_plugins": [],
			"mypy_version": "0.910",
			"tox_unmanaged": [],
			"yapf_exclude": [],
			"pre_commit_exclude": "xenial",
			"managed_message": "This file is managed by 'project_helper'. Don't edit it directly."
			}

	Additional options can be set and values changed at the start of tests as follows:

	.. code-block:: python

		def test(demo_environment):
			demo_environment.templates.globals["source_dir"] = "src"
	"""

	templates = Environment(
			loader=jinja2.FileSystemLoader(str(template_dir)),
			undefined=jinja2.StrictUndefined,
			)

	templates.globals.update({
			"author": "Bob & Alice",
			"email": "bob@example.com",
			"username": "octocat",
			"repo_name": "circuitpython_hello_world",
			"assignee": "octocat",
			"source_files": ["code.py", "boot.py", "secrets.py"],
			"additional_ignore": ["foo", "bar", "fuzz"],
			"imgbot_ignore": ["**/*.svg"],
			"exclude_files": [],
			"on_github": True,
			"mypy_deps": [],
			"mypy_plugins": [],
			"mypy_version": "0.910",
			"tox_unmanaged": [],
			"yapf_exclude": [],
			"pre_commit_exclude": "xenial",
			"managed_message": "This file is managed by 'project_helper'. Don't edit it directly.",
			"brace": brace,
			})

	return templates


FAKE_DATE = datetime.date(2020, 7, 25)


@pytest.fixture()
def temp_empty_repo(tmp_pathplus, monkeypatch) -> Repo:
	"""
	Pytest fixture to return an empty git repository in a temporary location.

	:data:`repo_helper.utils.today` is monkeypatched to return 25th July 2020.
	"""

	# Monkeypatch dulwich so it doesn't try to use the global config.
	monkeypatch.setattr(StackedConfig, "default_backends", lambda *args: [], raising=True)
	monkeypatch.setenv("GIT_COMMITTER_NAME", "Guido")
	monkeypatch.setenv("GIT_COMMITTER_EMAIL", "guido@python.org")
	monkeypatch.setenv("GIT_AUTHOR_NAME", "Guido")
	monkeypatch.setenv("GIT_AUTHOR_EMAIL", "guido@python.org")

	monkeypatch.setattr(repo_helper.utils, "today", FAKE_DATE)

	repo_dir = tmp_pathplus / secrets.token_hex(8)

	if sys.platform == "linux":
		repo_dir /= "%%tmp"

	repo_dir.maybe_make(parents=True)
	repo: Repo = Repo.init(repo_dir)
	return repo


@pytest.fixture()
def temp_repo(temp_empty_repo, example_config) -> Repo:
	"""
	Pytest fixture to return a git repository in a temporary location.

	The repository will contain a ``repo_helper.yml`` yaml file, the contents of which can be seen at
	https://github.com/domdfcoding/repo_helper/blob/master/repo_helper/testing/repo_helper_example.yml.

	:data:`repo_helper.utils.today` is monkeypatched to return 25th July 2020.
	"""

	(temp_empty_repo.path / "repo_helper.yml").write_text(example_config)

	return temp_empty_repo


@pytest.fixture(scope="session")
def example_config() -> str:
	"""
	Returns the contents of the example ``repo_helper.yml`` file.
	"""

	return (pathlib.Path(__file__).parent / "repo_helper_example.yml").read_text()


GITHUB_COM = URL("https://github.com")


def is_running_on_actions() -> bool:
	"""
	Returns :py:obj:`True` if running on GitHub Actions.
	"""

	# From https://github.com/ymyzk/tox-gh-actions
	# Copyright (c) 2019 Yusuke Miyazaki
	# MIT Licensed

	# See the following document on which environ to use for this purpose.
	# https://docs.github.com/en/free-pro-team@latest/actions/reference/environment-variables#default-environment-variables

	return "GITHUB_ACTIONS" in os.environ
