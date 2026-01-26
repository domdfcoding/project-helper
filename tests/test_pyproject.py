# stdlib
from typing import List

# 3rd party
import pytest
from coincidence.regressions import AdvancedFileRegressionFixture
from domdf_python_tools.paths import PathPlus
from repo_helper.templates import Environment

# this package
from project_helper.files.pyproject import make_pyproject


@pytest.mark.parametrize(
		"plugins",
		[
				pytest.param(["my.mypy:plugin"], id="with"),
				pytest.param([], id="without"),
				],
		)
def test_make_pyproject(
		tmp_pathplus: PathPlus,
		demo_environment: Environment,
		advanced_file_regression: AdvancedFileRegressionFixture,
		plugins: List[str],
		):

	demo_environment.globals["mypy_plugins"] = plugins

	managed_files = make_pyproject(tmp_pathplus, demo_environment)
	assert managed_files == ["pyproject.toml"]
	advanced_file_regression.check_file(tmp_pathplus / managed_files[0])
