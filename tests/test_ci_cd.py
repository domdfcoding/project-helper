# 3rd party
from coincidence import AdvancedFileRegressionFixture
from domdf_python_tools.paths import PathPlus
from repo_helper.templates import Environment

# this package
from project_helper.files.ci_cd import make_github_flake8, make_github_mypy


def test_make_github_flake8(
		tmp_pathplus: PathPlus,
		demo_environment: Environment,
		advanced_file_regression: AdvancedFileRegressionFixture,
		):
	assert make_github_flake8(tmp_pathplus, demo_environment) == [".github/workflows/flake8.yml"]
	assert (tmp_pathplus / ".github/workflows/flake8.yml").is_file()
	advanced_file_regression.check_file(tmp_pathplus / ".github/workflows/flake8.yml")


def test_make_github_mypy(
		tmp_pathplus: PathPlus,
		demo_environment: Environment,
		advanced_file_regression: AdvancedFileRegressionFixture,
		):
	assert make_github_mypy(tmp_pathplus, demo_environment) == [".github/workflows/mypy.yml"]
	assert (tmp_pathplus / ".github/workflows/mypy.yml").is_file()
	advanced_file_regression.check_file(tmp_pathplus / ".github/workflows/mypy.yml")
