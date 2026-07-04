from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pandas as pd

from economics.paths import repo_root


def test_build_cps_ipums_real_script_writes_real_output(tmp_path: Path) -> None:
    nominal_csv = tmp_path / "nominal.csv"
    price_index_csv = tmp_path / "annual_price_index.csv"
    output_csv = tmp_path / "real.csv"
    nominal_csv.write_text(
        "\n".join(
            [
                "year,value,series,source,variant,include_capital_gains,"
                "include_health_insurance,population,notes",
                "2023,100.0,Median adult-equivalent disposable resources,fixture,"
                "all_without_capital_gains_without_health_insurance,False,False,"
                "all,nominal fixture",
                "2024,200.0,Median adult-equivalent disposable resources,fixture,"
                "all_without_capital_gains_without_health_insurance,False,False,"
                "all,nominal fixture",
            ]
        )
        + "\n"
    )
    price_index_csv.write_text("year,price_index\n2023,100.0\n2024,125.0\n")

    result = subprocess.run(
        [
            sys.executable,
            str(repo_root() / "scripts" / "build_cps_ipums_real.py"),
            "--nominal-csv",
            str(nominal_csv),
            "--price-index-csv",
            str(price_index_csv),
            "--out",
            str(output_csv),
            "--base-year",
            "2024",
        ],
        cwd=repo_root(),
        check=True,
        capture_output=True,
        text=True,
    )

    out = pd.read_csv(output_csv)

    assert f"Wrote 2 real CPS/IPUMS rows to {output_csv}" in result.stdout
    assert list(out.columns) == [
        "year",
        "value",
        "nominal_value",
        "price_index",
        "real_base_year",
        "series",
        "source",
        "variant",
        "include_capital_gains",
        "include_health_insurance",
        "population",
        "notes",
    ]
    assert out[["year", "value", "nominal_value", "price_index", "real_base_year"]].to_dict(
        "records"
    ) == [
        {
            "year": 2023,
            "value": 125.0,
            "nominal_value": 100.0,
            "price_index": 100.0,
            "real_base_year": 2024,
        },
        {
            "year": 2024,
            "value": 200.0,
            "nominal_value": 200.0,
            "price_index": 125.0,
            "real_base_year": 2024,
        },
    ]
    assert "Converted to 2024 real dollars" in out["notes"].iloc[0]


def test_build_cps_ipums_real_script_reports_missing_price_index(tmp_path: Path) -> None:
    nominal_csv = tmp_path / "nominal.csv"
    missing_price_index_csv = tmp_path / "missing_price_index.csv"
    output_csv = tmp_path / "real.csv"
    nominal_csv.write_text("year,value\n2024,200.0\n")

    result = subprocess.run(
        [
            sys.executable,
            str(repo_root() / "scripts" / "build_cps_ipums_real.py"),
            "--nominal-csv",
            str(nominal_csv),
            "--price-index-csv",
            str(missing_price_index_csv),
            "--out",
            str(output_csv),
        ],
        cwd=repo_root(),
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert f"Expected annual price-index file not found: {missing_price_index_csv}" in result.stderr
    assert not output_csv.exists()
