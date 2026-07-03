from pathlib import Path

import pandas as pd
import pytest

from economics.charts import plot_time_series
from economics.loaders import load_comparison_series
from economics.paths import processed_data_path
from economics.tables import build_summary_table


def test_build_summary_table_returns_named_metric_rows() -> None:
    df = pd.DataFrame({"year": [2000, 2002], "value": [100, 121]})

    table = build_summary_table(df, "value", label="Test series")
    records = table.to_dict("records")

    assert records[:5] == [
        {"series": "Test series", "metric": "start_year", "value": 2000.0},
        {"series": "Test series", "metric": "end_year", "value": 2002.0},
        {"series": "Test series", "metric": "start_value", "value": 100.0},
        {"series": "Test series", "metric": "end_value", "value": 121.0},
        {"series": "Test series", "metric": "cumulative_growth_pct", "value": 21.0},
    ]
    assert records[5] == {
        "series": "Test series",
        "metric": "annualized_growth_pct",
        "value": pytest.approx(10.0),
    }


def test_plot_time_series_writes_chart_file(tmp_path: Path) -> None:
    df = pd.DataFrame({"year": [2000, 2001], "value": [100, 105]})
    output_path = tmp_path / "chart.png"

    fig, ax = plot_time_series(
        df,
        "value",
        title="Test title",
        ylabel="Test dollars",
        output_path=output_path,
    )

    assert output_path.exists()
    assert ax.get_title() == "Test title"
    assert ax.get_xlabel() == "Year"
    assert ax.get_ylabel() == "Test dollars"
    fig.clear()


def test_plot_multiple_series_writes_chart_file(tmp_path: Path) -> None:
    from economics.charts import plot_multiple_series

    df = pd.DataFrame(
        {
            "year": [2020, 2021, 2020, 2021],
            "value": [100, 105, 80, 84],
            "series": ["Series A", "Series A", "Series B", "Series B"],
        }
    )
    output_path = tmp_path / "multi.png"

    fig, ax = plot_multiple_series(
        df,
        title="Comparison",
        ylabel="Dollars",
        output_path=output_path,
    )

    assert output_path.exists()
    assert ax.get_title() == "Comparison"
    assert len(ax.lines) == 2
    fig.clear()


def test_bundled_fred_comparison_files_exist_and_load() -> None:
    expected = [
        "fred_real_median_personal_income.csv",
        "fred_real_median_household_income.csv",
        "fred_real_disposable_personal_income_per_capita.csv",
    ]

    for filename in expected:
        path = processed_data_path(filename)
        assert path.exists()

        df = load_comparison_series(path)
        raw = pd.read_csv(path)

        assert list(raw.columns) == ["year", "value", "series_id", "series", "source", "notes"]
        assert df["year"].is_monotonic_increasing
        assert not df.empty
