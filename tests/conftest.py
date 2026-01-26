# 3rd party
import jinja2
import pytest  # nodep
from repo_helper.templates import Environment
from repo_helper.utils import brace

# this package
from project_helper.templates import template_dir

pytest_plugins = ("coincidence", )


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
