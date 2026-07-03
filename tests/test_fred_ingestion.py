from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from economics.fred import FRED_SERIES, build_all_fred_series, build_fred_series
from economics.paths import repo_root


def test_build_fred_series_reads_fred_graph_csv(tmp_path: Path) -> None:
    raw = tmp_path / "mepain.csv"
    raw.write_text(
        "\n".join(
            [
                "observation_date,MEPAINUSA672N",
                "2021-01-01,43080",
                "2020-01-01,43010",
            ]
        )
    )

    df = build_fred_series(raw, FRED_SERIES["real_median_personal_income"])

    assert df.to_dict("records") == [
        {
            "year": 2020,
            "value": 43010.0,
            "series_id": "MEPAINUSA672N",
            "series": "Real median personal income",
            "source": "FRED/Census MEPAINUSA672N",
            "notes": "2024 C-CPI-U dollars; annual; not seasonally adjusted.",
        },
        {
            "year": 2021,
            "value": 43080.0,
            "series_id": "MEPAINUSA672N",
            "series": "Real median personal income",
            "source": "FRED/Census MEPAINUSA672N",
            "notes": "2024 C-CPI-U dollars; annual; not seasonally adjusted.",
        },
    ]


def test_build_fred_series_reads_project_shaped_csv(tmp_path: Path) -> None:
    raw = tmp_path / "household.csv"
    raw.write_text("year,value\n2024,83730\n2023,82690\n")

    df = build_fred_series(raw, FRED_SERIES["real_median_household_income"])

    assert df[["year", "value"]].to_dict("records") == [
        {"year": 2023, "value": 82690.0},
        {"year": 2024, "value": 83730.0},
    ]
    assert df["series"].unique().tolist() == ["Real median household income"]


def test_build_fred_series_reads_date_value_csv(tmp_path: Path) -> None:
    raw = tmp_path / "household.csv"
    raw.write_text("DATE,value\n2024-01-01,83730\n")

    df = build_fred_series(raw, FRED_SERIES["real_median_household_income"])

    assert df[["year", "value", "series_id"]].to_dict("records") == [
        {"year": 2024, "value": 83730.0, "series_id": "MEHOINUSA672N"}
    ]


def test_build_fred_series_averages_monthly_full_years_and_drops_incomplete_years(
    tmp_path: Path,
) -> None:
    raw = tmp_path / "disposable.csv"
    rows = ["observation_date,A229RX0"]
    rows.extend(f"2020-{month:02d}-01,{1200 + month}" for month in range(1, 13))
    rows.extend(f"2021-{month:02d}-01,{1300 + month}" for month in range(1, 6))
    raw.write_text("\n".join(rows))

    df = build_fred_series(raw, FRED_SERIES["real_disposable_personal_income_per_capita"])

    assert df[["year", "value"]].to_dict("records") == [
        {"year": 2020, "value": pytest.approx(1206.5)}
    ]


def test_build_fred_series_keeps_project_shaped_disposable_income(tmp_path: Path) -> None:
    raw = tmp_path / "disposable.csv"
    raw.write_text("year,value\n2020,1206.5\n2021,1306.5\n")

    df = build_fred_series(raw, FRED_SERIES["real_disposable_personal_income_per_capita"])

    assert df[["year", "value"]].to_dict("records") == [
        {"year": 2020, "value": 1206.5},
        {"year": 2021, "value": 1306.5},
    ]


def test_build_fred_series_requires_distinct_months_for_monthly_full_years(
    tmp_path: Path,
) -> None:
    raw = tmp_path / "disposable.csv"
    rows = ["observation_date,A229RX0"]
    rows.extend(f"2020-{month:02d}-01,{1200 + month}" for month in range(1, 12))
    rows.append("2020-11-15,1211")
    raw.write_text("\n".join(rows))

    df = build_fred_series(raw, FRED_SERIES["real_disposable_personal_income_per_capita"])

    assert df.empty


def test_build_fred_series_averages_duplicate_months_before_annual_mean(
    tmp_path: Path,
) -> None:
    raw = tmp_path / "disposable.csv"
    rows = ["observation_date,A229RX0", "2020-01-01,100", "2020-01-15,300"]
    rows.extend(f"2020-{month:02d}-01,100" for month in range(2, 13))
    raw.write_text("\n".join(rows))

    df = build_fred_series(raw, FRED_SERIES["real_disposable_personal_income_per_capita"])

    assert df[["year", "value"]].to_dict("records") == [
        {"year": 2020, "value": pytest.approx(108.33333333333333)}
    ]


def test_build_fred_series_drops_fred_missing_value_markers(tmp_path: Path) -> None:
    raw = tmp_path / "mepain.csv"
    raw.write_text("observation_date,MEPAINUSA672N\n2020-01-01,.\n2021-01-01,43080\n")

    df = build_fred_series(raw, FRED_SERIES["real_median_personal_income"])

    assert df[["year", "value"]].to_dict("records") == [{"year": 2021, "value": 43080.0}]


def test_build_fred_series_reports_missing_columns(tmp_path: Path) -> None:
    raw = tmp_path / "bad.csv"
    raw.write_text("date,wrong\n2020-01-01,1\n")

    with pytest.raises(ValueError, match="expected either columns"):
        build_fred_series(raw, FRED_SERIES["real_median_personal_income"])


def test_build_all_fred_series_writes_processed_outputs(tmp_path: Path) -> None:
    raw_dir = tmp_path / "raw"
    processed_dir = tmp_path / "processed"
    raw_dir.mkdir()
    (raw_dir / "fred_real_median_personal_income.csv").write_text(
        "observation_date,MEPAINUSA672N\n2024-01-01,45140\n"
    )
    (raw_dir / "fred_real_median_household_income.csv").write_text(
        "observation_date,MEHOINUSA672N\n2024-01-01,83730\n"
    )
    (raw_dir / "fred_real_disposable_personal_income_per_capita.csv").write_text(
        "\n".join(
            [
                "observation_date,A229RX0",
                *[f"2024-{month:02d}-01,100" for month in range(1, 13)],
            ]
        )
    )

    outputs = build_all_fred_series(raw_dir, processed_dir)

    assert sorted(outputs) == [
        "real_disposable_personal_income_per_capita",
        "real_median_household_income",
        "real_median_personal_income",
    ]
    for output_path in outputs.values():
        assert output_path.exists()


def test_build_fred_comparisons_script_writes_processed_csvs(tmp_path: Path) -> None:
    raw_dir = tmp_path / "raw"
    processed_dir = tmp_path / "processed"
    raw_dir.mkdir()
    (raw_dir / "fred_real_median_personal_income.csv").write_text(
        "observation_date,MEPAINUSA672N\n2024-01-01,45140\n"
    )
    (raw_dir / "fred_real_median_household_income.csv").write_text(
        "observation_date,MEHOINUSA672N\n2024-01-01,83730\n"
    )
    (raw_dir / "fred_real_disposable_personal_income_per_capita.csv").write_text(
        "\n".join(
            [
                "observation_date,A229RX0",
                *[f"2024-{month:02d}-01,100" for month in range(1, 13)],
            ]
        )
    )

    result = subprocess.run(
        [
            sys.executable,
            str(repo_root() / "scripts" / "build_fred_comparisons.py"),
            "--raw-dir",
            str(raw_dir),
            "--processed-dir",
            str(processed_dir),
        ],
        cwd=repo_root(),
        check=True,
        capture_output=True,
        text=True,
    )

    assert "Wrote 3 FRED comparison files" in result.stdout
    assert (processed_dir / "fred_real_median_personal_income.csv").exists()
