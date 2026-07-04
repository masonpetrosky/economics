from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest

from economics.paths import repo_root
from economics.proxy_qa import build_indexed_common_overlap


def test_build_indexed_common_overlap_indexes_every_series_to_common_start() -> None:
    frames = {
        "Series A": pd.DataFrame({"year": [2000, 2001, 2002], "value": [50.0, 100.0, 110.0]}),
        "Series B": pd.DataFrame({"year": [2001, 2002, 2003], "value": [80.0, 120.0, 160.0]}),
    }

    out = build_indexed_common_overlap(frames)

    assert out.to_dict("records") == [
        {
            "year": 2001,
            "series": "Series A",
            "value": 100.0,
            "index_value": 100.0,
            "common_start_year": 2001,
            "common_end_year": 2002,
        },
        {
            "year": 2002,
            "series": "Series A",
            "value": 110.0,
            "index_value": 110.0,
            "common_start_year": 2001,
            "common_end_year": 2002,
        },
        {
            "year": 2001,
            "series": "Series B",
            "value": 80.0,
            "index_value": 100.0,
            "common_start_year": 2001,
            "common_end_year": 2002,
        },
        {
            "year": 2002,
            "series": "Series B",
            "value": 120.0,
            "index_value": 150.0,
            "common_start_year": 2001,
            "common_end_year": 2002,
        },
    ]


def test_build_indexed_common_overlap_rejects_no_common_overlap() -> None:
    frames = {
        "Series A": pd.DataFrame({"year": [2000], "value": [50.0]}),
        "Series B": pd.DataFrame({"year": [2001], "value": [80.0]}),
    }

    with pytest.raises(ValueError, match="No common overlap exists across the supplied series"):
        build_indexed_common_overlap(frames)


def test_build_cps_public_proxy_qa_script_writes_table_and_chart(tmp_path: Path) -> None:
    processed_dir = tmp_path / "processed"
    table_out = tmp_path / "qa.csv"
    chart_out = tmp_path / "qa.png"
    processed_dir.mkdir()

    (processed_dir / "cps_ipums_median_adult_equivalent_resources_real.csv").write_text(
        "\n".join(
            [
                "year,value,nominal_value,price_index,real_base_year,series,source,"
                "variant,include_capital_gains,include_health_insurance,population,notes",
                "2021,100.0,90.0,90.0,2024,"
                "Median adult-equivalent disposable resources,fixture,cps,False,False,"
                "all,fixture",
                "2022,110.0,105.0,95.0,2024,"
                "Median adult-equivalent disposable resources,fixture,cps,False,False,"
                "all,fixture",
            ]
        )
        + "\n"
    )
    (processed_dir / "cbo_proxy_median_adjusted_income_after_tax_transfer.csv").write_text(
        "year,median_adjusted_income_after_transfers_taxes_2022_dollars,source,notes\n"
        "2021,200.0,fixture,fixture\n"
        "2022,220.0,fixture,fixture\n"
    )
    for filename, series_name, start, end in [
        ("fred_real_median_personal_income.csv", "Real median personal income", 50.0, 55.0),
        ("fred_real_median_household_income.csv", "Real median household income", 80.0, 84.0),
        (
            "fred_real_disposable_personal_income_per_capita.csv",
            "Real disposable personal income per capita",
            70.0,
            77.0,
        ),
    ]:
        (processed_dir / filename).write_text(
            "year,value,series_id,series,source,notes\n"
            f"2021,{start},TEST,{series_name},fixture,fixture\n"
            f"2022,{end},TEST,{series_name},fixture,fixture\n"
        )

    result = subprocess.run(
        [
            sys.executable,
            str(repo_root() / "scripts" / "build_cps_public_proxy_qa.py"),
            "--processed-dir",
            str(processed_dir),
            "--table-out",
            str(table_out),
            "--chart-out",
            str(chart_out),
        ],
        cwd=repo_root(),
        check=True,
        capture_output=True,
        text=True,
    )

    table = pd.read_csv(table_out)

    assert f"Wrote 10 QA rows to {table_out}" in result.stdout
    assert f"Saved QA chart to {chart_out}" in result.stdout
    assert chart_out.exists()
    assert list(table.columns) == [
        "year",
        "series",
        "value",
        "index_value",
        "common_start_year",
        "common_end_year",
    ]
    assert set(table["series"]) == {
        "CBO adjusted income after transfers and taxes",
        "Median adult-equivalent disposable resources",
        "Real disposable personal income per capita",
        "Real median household income",
        "Real median personal income",
    }
    assert table["common_start_year"].unique().tolist() == [2021]
    assert table["common_end_year"].unique().tolist() == [2022]
