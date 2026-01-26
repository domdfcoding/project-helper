#!/usr/bin/env python
#
#  gitignore.py
"""
Configuration for the ``.gitignore`` file.
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
from typing import List

# 3rd party
from domdf_python_tools.paths import PathPlus
from repo_helper.templates import Environment

# this package
from project_helper.files import management

__all__ = [
		"ignores",
		"make_gitignore",
		]

ignores: List[str] = []

# Byte-compiled / optimized / DLL files
ignores.extend((
		"__pycache__/",
		"*.py[cod]",
		"*$py.class",
		))

# C extensions
ignores.extend(("*.so", ))

# Distribution / packaging
ignores.extend((
		".Python",
		"build/",
		"develop-eggs/",
		"dist/",
		"downloads/",
		"eggs/",
		".eggs/",
		"lib/",
		"lib64/",
		"parts/",
		"sdist/",
		"var/",
		"wheels/",
		"*.egg-info/",
		".installed.cfg",
		"*.egg",
		"*.egg*",
		))

# PyInstaller
#  Usually these files are written by a python script from a template
#  before PyInstaller builds the exe, so as to inject date/other infos into it.
ignores.extend((
		"*.manifest",
		"*.spec",
		))

# Installer logs
ignores.extend((
		"pip-log.txt",
		"pip-delete-this-directory.txt",
		))

# Unit test / coverage reports
ignores.extend((
		"htmlcov/",
		".tox/",
		".coverage",
		".coverage.*",
		".cache",
		"nosetests.xml",
		"coverage.xml",
		"*.cover",
		".hypothesis/",
		".pytest_cache/",
		"cover/",
		))

# Translations
ignores.extend((
		"*.mo",
		"*.pot",
		))

# Django stuff:
ignores.extend((
		"*.log",
		"local_settings.py",
		"db.sqlite3",
		))

# Flask stuff:
ignores.extend((
		"instance/",
		".webassets-cache",
		))

# Scrapy stuff:
ignores.extend((".scrapy", ))

# Sphinx documentation
ignores.extend((
		"docs/_build/",
		"doc/build",
		))

# PyBuilder
ignores.extend([
		"target/",
		])

# Jupyter Notebook
ignores.extend((".ipynb_checkpoints", ))

# pyenv
ignores.extend((".python-version", ))

# celery beat schedule file
ignores.extend((
		"celerybeat-schedule",
		"celerybeat.pid",
		))

# SageMath parsed files
ignores.extend(("*.sage.py", ))

# Environments
ignores.extend((
		".env",
		".venv",
		"env/",
		"venv/",
		"ENV/",
		"env.bak/",
		"venv.bak/",
		))

# Spyder project settings
ignores.extend((
		".spyderproject",
		".spyproject",
		))

# Rope project settings
ignores.extend((".ropeproject", ))

# mkdocs documentation
ignores.extend(("/site", ))

# mypy
ignores.extend((
		".mypy_cache/",
		".dmypy.json",
		"dmypy.json",
		))

# Covers JetBrains IDEs: IntelliJ, RubyMine, PhpStorm, AppCode, PyCharm, CLion, Android Studio, WebStorm and Rider
# Reference: https://intellij-support.jetbrains.com/hc/en-us/articles/206544839

# Gradle
ignores.extend((
		"*.iml",
		"*.ipr",
		))

# CMake
ignores.extend(("cmake-build-*/", ))

# Mongo Explorer plugin
ignores.extend((".idea/**/mongoSettings.xml", ))

# File-based project format
ignores.extend(("*.iws", ))

# IntelliJ
ignores.extend(("out/", ))

# JIRA plugin
ignores.extend(("atlassian-ide-plugin.xml", ))

# Crashlytics plugin (for Android Studio and IntelliJ)
ignores.extend((
		"com_crashlytics_export_strings.xml",
		"crashlytics.properties",
		"crashlytics-build.properties",
		"fabric.properties",
		))

ignores.extend((
		".idea",
		"build",
		"**/__pycache__",
		"**/conda",
		"__pypackages__/",
		"profile_default/",
		"ipython_config.py",
		"Pipfile.lock",
		".pyre/",
		))


@management.register("gitignore")
def make_gitignore(project: pathlib.Path, templates: Environment) -> List[str]:
	"""
	Add .gitignore file to the given repository.

	:param project: Path to the project root.
	:param templates:
	"""

	all_ignores = [
			f"# {templates.globals['managed_message']}",
			*ignores,
			*templates.globals["additional_ignore"],
			]

	PathPlus(project / ".gitignore").write_clean('\n'.join(all_ignores))

	return [".gitignore"]
