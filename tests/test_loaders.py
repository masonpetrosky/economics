from pathlib import Path

import pandas as pd
import pytest

from economics.loaders import (
    CBO_PROXY_VALUE_COL,
    load_cbo_proxy,
    load_comparison_series,
    validate_required_columns,
)
from economics.paths import processed_data_path, repo_root


def test_repo_root_points_to_project_directory() -> None:
    assert (repo_root() / "README.md").exists()


def test_processed_data_path_builds_repo_relative_path() -> None:
    path = processed_data_path("cbo_proxy_median_adjusted_income_after_tax_transfer.csv")
    assert path == repo_root() / "data" / "processed" / path.name


def test_validate_required_columns_reports_missing_columns() -> None:
    df = pd.DataFrame({"year": [2020]})

    with pytest.raises(ValueError, match="starter file missing required columns: \\['value'\\]"):
        validate_required_columns(df, ["year", "value"], "starter file")


def test_load_cbo_proxy_reads_bundled_starter_series() -> None:
    path = processed_data_path("cbo_proxy_median_adjusted_income_after_tax_transfer.csv")

    df = load_cbo_proxy(path)

    assert list(df.columns[:2]) == ["year", CBO_PROXY_VALUE_COL]
    assert df["year"].iloc[0] == 1979
    assert df["year"].iloc[-1] == 2022


def test_load_cbo_proxy_rejects_missing_value_column(tmp_path: Path) -> None:
    bad_path = tmp_path / "bad_cbo.csv"
    pd.DataFrame({"year": [2020], "wrong": [1]}).to_csv(bad_path, index=False)

    with pytest.raises(ValueError, match=CBO_PROXY_VALUE_COL):
        load_cbo_proxy(bad_path)


def test_load_comparison_series_normalizes_to_year_value_and_series(tmp_path: Path) -> None:
    path = tmp_path / "comparison.csv"
    pd.DataFrame({"year": [2021, 2020], "median": [12, 10]}).to_csv(path, index=False)

    df = load_comparison_series(path, value_col="median", series_name="Real median test")

    assert df.to_dict("records") == [
        {"year": 2020, "value": 10, "series": "Real median test"},
        {"year": 2021, "value": 12, "series": "Real median test"},
    ]
