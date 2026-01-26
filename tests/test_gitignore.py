# 3rd party
from coincidence.regressions import check_file_output
from domdf_python_tools.paths import PathPlus
from pytest_regressions.file_regression import FileRegressionFixture
from repo_helper.templates import Environment

# this package
from project_helper.files.gitignore import make_gitignore


def test_make_gitignore(
		tmp_pathplus: PathPlus,
		demo_environment: Environment,
		file_regression: FileRegressionFixture,
		):
	managed_files = make_gitignore(tmp_pathplus, demo_environment)
	assert managed_files == [".gitignore"]
	check_file_output(tmp_pathplus / managed_files[0], file_regression)
