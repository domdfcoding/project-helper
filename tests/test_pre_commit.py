# 3rd party
from coincidence.regressions import AdvancedFileRegressionFixture
from domdf_python_tools.paths import PathPlus
from repo_helper.templates import Environment

# this package
from project_helper.files.pre_commit import make_pre_commit


def test_make_pre_commit(
		tmp_pathplus: PathPlus,
		demo_environment: Environment,
		advanced_file_regression: AdvancedFileRegressionFixture,
		):

	# TODO: Test with a custom hook after the comment

	demo_environment.globals["yapf_exclude"] = []
	demo_environment.globals["pre_commit_exclude"] = "^$"

	(tmp_pathplus / ".pre-commit-config.yaml").touch()

	managed_files = make_pre_commit(tmp_pathplus, demo_environment)
	assert managed_files == [".pre-commit-config.yaml"]
	advanced_file_regression.check_file(tmp_pathplus / managed_files[0])
