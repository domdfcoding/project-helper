# stdlib
from typing import Sequence

# 3rd party
import pytest
from coincidence import AdvancedFileRegressionFixture
from domdf_python_tools.paths import PathPlus

# this package
from project_helper.files.qa import make_formate_toml, make_pylintrc, make_tox, make_yapf


def test_make_formate_toml_case_1(
		tmp_pathplus: PathPlus,
		demo_environment,
		advanced_file_regression: AdvancedFileRegressionFixture,
		):
	(tmp_pathplus / "tests").mkdir()
	(tmp_pathplus / "tests" / "requirements.txt").write_text('')

	(tmp_pathplus / "requirements.txt").write_lines([
			"tox",
			"isort",
			"black",
			"wheel",
			"setuptools_rust",
			])

	managed_files = make_formate_toml(tmp_pathplus, demo_environment)
	assert managed_files == ["formate.toml"]
	advanced_file_regression.check_file(tmp_pathplus / managed_files[0])


def test_make_formate_toml_case_2(
		tmp_pathplus: PathPlus,
		demo_environment,
		advanced_file_regression: AdvancedFileRegressionFixture,
		):
	(tmp_pathplus / "tests").mkdir()
	(tmp_pathplus / "tests" / "requirements.txt").write_text('')

	(tmp_pathplus / "requirements.txt").write_lines([
			"tox",
			"isort",
			"black",
			"wheel",
			"setuptools_rust",
			])

	(tmp_pathplus / ".isort.cfg").write_lines(["[settings]", "known_third_party=awesome_package"])

	managed_files = make_formate_toml(tmp_pathplus, demo_environment)
	assert managed_files == ["formate.toml"]
	advanced_file_regression.check_file(tmp_pathplus / managed_files[0])


def test_make_formate_toml_case_3(
		tmp_pathplus: PathPlus,
		demo_environment,
		advanced_file_regression: AdvancedFileRegressionFixture,
		):
	(tmp_pathplus / "tests").mkdir()
	(tmp_pathplus / "tests" / "requirements.txt").write_text('')

	(tmp_pathplus / "requirements.txt").write_lines([
			"tox",
			"isort",
			"black",
			"wheel",
			"setuptools_rust",
			])

	(tmp_pathplus / "formate.toml").write_lines([
			"[hooks.isort.kwargs]",
			'known_third_party = ["awesome_package"]',
			])

	managed_files = make_formate_toml(tmp_pathplus, demo_environment)
	assert managed_files == ["formate.toml"]
	advanced_file_regression.check_file(tmp_pathplus / managed_files[0])


def test_pylintrc(
		tmp_pathplus: PathPlus,
		demo_environment,
		advanced_file_regression: AdvancedFileRegressionFixture,
		):
	managed_files = make_pylintrc(tmp_pathplus, demo_environment)
	assert managed_files == [".pylintrc"]
	advanced_file_regression.check_file(tmp_pathplus / managed_files[0])


def test_make_yapf(
		tmp_pathplus: PathPlus,
		demo_environment,
		advanced_file_regression: AdvancedFileRegressionFixture,
		):
	managed_files = make_yapf(tmp_pathplus, demo_environment)
	assert managed_files == [".style.yapf"]
	advanced_file_regression.check_file(tmp_pathplus / managed_files[0])


class TestMakeTox:

	@staticmethod
	def set_globals(
			demo_environment,
			mypy_deps: Sequence[str] = (),
			mypy_version: str = "0.790",
			tox_unmanaged: Sequence[str] = (),
			yapf_exclude: Sequence[str] = (),
			):
		demo_environment.globals["mypy_deps"] = list(mypy_deps)
		demo_environment.globals["mypy_version"] = mypy_version
		demo_environment.globals["tox_unmanaged"] = list(tox_unmanaged)
		demo_environment.globals["yapf_exclude"] = list(yapf_exclude)

	@pytest.mark.parametrize("mypy_deps", [[], ["docutils-stubs"]])
	def test_tox_mypy_deps(
			self,
			tmp_pathplus: PathPlus,
			demo_environment,
			advanced_file_regression: AdvancedFileRegressionFixture,
			mypy_deps,
			):
		self.set_globals(demo_environment, mypy_deps=mypy_deps)
		make_tox(tmp_pathplus, demo_environment)
		advanced_file_regression.check_file(tmp_pathplus / "tox.ini")

	@pytest.mark.parametrize("mypy_version", ["0.790", "0.782"])
	def test_tox_mypy_version(
			self,
			tmp_pathplus: PathPlus,
			demo_environment,
			advanced_file_regression: AdvancedFileRegressionFixture,
			mypy_version,
			):
		self.set_globals(demo_environment, mypy_version=mypy_version)
		make_tox(tmp_pathplus, demo_environment)
		advanced_file_regression.check_file(tmp_pathplus / "tox.ini")
