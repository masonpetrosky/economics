from pathlib import Path

import pandas as pd
import pytest

from economics.charts import plot_time_series
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
