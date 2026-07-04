from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest

from economics.cps import (
    CpsVariant,
    build_cps_person_resources,
    estimate_cps_annual_medians,
    normalize_ipums_cps_asec_extract,
    validate_cps_columns,
)
from economics.paths import repo_root


def cps_fixture() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "year": 2020,
                "serial": 1,
                "pernum": 1,
                "age": 10,
                "asecwt": 5,
                "household_size": 1,
                "money_income": 10_000,
                "realized_capital_gains": 1_000,
                "noncash_benefits": 0,
                "health_insurance_value": 0,
                "federal_income_taxes": 0,
                "payroll_taxes": 0,
                "state_local_income_taxes": 0,
            },
            {
                "year": 2020,
                "serial": 2,
                "pernum": 1,
                "age": 30,
                "asecwt": 1,
                "household_size": 1,
                "money_income": 50_000,
                "realized_capital_gains": 10_000,
                "noncash_benefits": 0,
                "health_insurance_value": 5_000,
                "federal_income_taxes": 3_000,
                "payroll_taxes": 1_500,
                "state_local_income_taxes": 500,
            },
            {
                "year": 2021,
                "serial": 3,
                "pernum": 1,
                "age": 40,
                "asecwt": 1,
                "household_size": 4,
                "money_income": 80_000,
                "realized_capital_gains": 0,
                "noncash_benefits": 0,
                "health_insurance_value": 0,
                "federal_income_taxes": 0,
                "payroll_taxes": 0,
                "state_local_income_taxes": 0,
            },
        ]
    )


def test_validate_cps_columns_reports_missing_columns() -> None:
    df = cps_fixture().drop(columns=["age"])

    with pytest.raises(ValueError, match="CPS fixture missing required columns: \\['age'\\]"):
        validate_cps_columns(df, source_label="CPS fixture")


def test_build_cps_person_resources_applies_components_and_equivalence() -> None:
    rows = build_cps_person_resources(cps_fixture(), CpsVariant(population="adults"))

    assert rows[["year", "pernum", "comprehensive_resources", "equivalized_resources"]].to_dict(
        "records"
    ) == [
        {
            "year": 2020,
            "pernum": 1,
            "comprehensive_resources": 60_000.0,
            "equivalized_resources": 60_000.0,
        },
        {
            "year": 2021,
            "pernum": 1,
            "comprehensive_resources": 80_000.0,
            "equivalized_resources": 40_000.0,
        },
    ]


def test_estimate_cps_annual_medians_uses_person_weights_by_year() -> None:
    medians = estimate_cps_annual_medians(cps_fixture())

    assert medians[["year", "value", "variant", "population"]].to_dict("records") == [
        {
            "year": 2020,
            "value": 11_000.0,
            "variant": "all_with_capital_gains_with_health_insurance",
            "population": "all",
        },
        {
            "year": 2021,
            "value": 40_000.0,
            "variant": "all_with_capital_gains_with_health_insurance",
            "population": "all",
        },
    ]
    assert medians["series"].unique().tolist() == [
        "Median adult-equivalent disposable resources"
    ]
    assert medians["source"].unique().tolist() == ["CPS ASEC/IPUMS normalized extract"]


def test_estimate_cps_annual_medians_rejects_duplicate_person_rows() -> None:
    df = pd.concat([cps_fixture(), cps_fixture().iloc[[1]]], ignore_index=True)

    with pytest.raises(ValueError, match="Duplicate CPS person rows") as exc_info:
        estimate_cps_annual_medians(df)

    assert "2020" in str(exc_info.value)


def test_estimate_cps_annual_medians_supports_adult_population_filter() -> None:
    medians = estimate_cps_annual_medians(cps_fixture(), CpsVariant(population="adults"))

    assert medians[["year", "value", "population"]].to_dict("records") == [
        {"year": 2020, "value": 60_000.0, "population": "adults"},
        {"year": 2021, "value": 40_000.0, "population": "adults"},
    ]


def test_estimate_cps_annual_medians_supports_capital_gains_and_health_toggles() -> None:
    variant = CpsVariant(
        include_capital_gains=False,
        include_health_insurance=False,
        population="adults",
    )

    medians = estimate_cps_annual_medians(cps_fixture(), variant)

    assert medians[["year", "value", "variant"]].to_dict("records") == [
        {
            "year": 2020,
            "value": 45_000.0,
            "variant": "adults_without_capital_gains_without_health_insurance",
        },
        {
            "year": 2021,
            "value": 40_000.0,
            "variant": "adults_without_capital_gains_without_health_insurance",
        },
    ]


def test_estimate_cps_annual_medians_drops_invalid_weights_and_household_sizes() -> None:
    df = pd.concat(
        [
            cps_fixture(),
            pd.DataFrame(
                [
                    {
                        "year": 2020,
                        "serial": 9,
                        "pernum": 1,
                        "age": 60,
                        "asecwt": 0,
                        "household_size": 1,
                        "money_income": 1,
                        "realized_capital_gains": 0,
                        "noncash_benefits": 0,
                        "health_insurance_value": 0,
                        "federal_income_taxes": 0,
                        "payroll_taxes": 0,
                        "state_local_income_taxes": 0,
                    },
                    {
                        "year": 2020,
                        "serial": 10,
                        "pernum": 1,
                        "age": 60,
                        "asecwt": 100,
                        "household_size": 0,
                        "money_income": 1,
                        "realized_capital_gains": 0,
                        "noncash_benefits": 0,
                        "health_insurance_value": 0,
                        "federal_income_taxes": 0,
                        "payroll_taxes": 0,
                        "state_local_income_taxes": 0,
                    },
                ]
            ),
        ],
        ignore_index=True,
    )

    medians = estimate_cps_annual_medians(df)

    assert medians.loc[medians["year"] == 2020, "value"].iloc[0] == 11_000.0


def test_estimate_cps_annual_medians_rejects_years_lost_to_invalid_rows() -> None:
    df = pd.concat(
        [
            cps_fixture(),
            pd.DataFrame(
                [
                    {
                        "year": 2022,
                        "serial": 11,
                        "pernum": 1,
                        "age": 60,
                        "asecwt": 0,
                        "household_size": 1,
                        "money_income": 50_000,
                        "realized_capital_gains": 0,
                        "noncash_benefits": 0,
                        "health_insurance_value": 0,
                        "federal_income_taxes": 0,
                        "payroll_taxes": 0,
                        "state_local_income_taxes": 0,
                    },
                ]
            ),
        ],
        ignore_index=True,
    )

    with pytest.raises(ValueError, match="2022"):
        estimate_cps_annual_medians(df)


def test_estimate_cps_annual_medians_rejects_years_lost_to_adult_filter() -> None:
    df = cps_fixture()
    df.loc[df["year"] == 2020, "age"] = 10

    with pytest.raises(ValueError, match="2020"):
        estimate_cps_annual_medians(df, CpsVariant(population="adults"))


def test_estimate_cps_annual_medians_ignores_missing_excluded_components() -> None:
    df = cps_fixture()
    adult_2020 = (df["year"] == 2020) & (df["age"] >= 18)
    df.loc[adult_2020, "realized_capital_gains"] = pd.NA
    df.loc[adult_2020, "health_insurance_value"] = pd.NA
    variant = CpsVariant(
        include_capital_gains=False,
        include_health_insurance=False,
        population="adults",
    )

    medians = estimate_cps_annual_medians(df, variant)

    assert medians.loc[medians["year"] == 2020, "value"].iloc[0] == 45_000.0


def test_estimate_cps_annual_medians_rejects_empty_filtered_data() -> None:
    df = cps_fixture()
    df["asecwt"] = 0

    with pytest.raises(
        ValueError,
        match="No CPS observations remain after filtering invalid weights and household sizes",
    ):
        estimate_cps_annual_medians(df)


def test_cps_variant_rejects_unknown_population() -> None:
    with pytest.raises(ValueError, match="population must be one of: all, adults"):
        CpsVariant(population="children")


def ipums_raw_fixture() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "YEAR": 2021,
                "SERIAL": 100,
                "PERNUM": 1,
                "AGE": 35,
                "ASECWT": 2.5,
                "NUMPREC": 2,
                "HHINCOME": 80_000,
                "CAPGAIN": 5_000,
                "FEDTAX": 6_000,
                "FICA": 3_000,
                "STATETAX": 1_000,
            },
            {
                "YEAR": 2022,
                "SERIAL": 200,
                "PERNUM": 1,
                "AGE": 42,
                "ASECWT": 1.0,
                "NUMPREC": 4,
                "HHINCOME": 120_000,
                "CAPGAIN": 0,
                "FEDTAX": 8_000,
                "FICA": 4_000,
                "STATETAX": 2_000,
            },
        ]
    )


def test_normalize_ipums_cps_asec_extract_maps_official_columns() -> None:
    normalized = normalize_ipums_cps_asec_extract(ipums_raw_fixture())

    assert normalized.to_dict("records") == [
        {
            "year": 2020,
            "serial": 100,
            "pernum": 1,
            "age": 35,
            "asecwt": 2.5,
            "household_size": 2,
            "money_income": 80_000,
            "realized_capital_gains": 5_000,
            "noncash_benefits": 0.0,
            "health_insurance_value": 0.0,
            "federal_income_taxes": 6_000,
            "payroll_taxes": 3_000,
            "state_local_income_taxes": 1_000,
        },
        {
            "year": 2021,
            "serial": 200,
            "pernum": 1,
            "age": 42,
            "asecwt": 1.0,
            "household_size": 4,
            "money_income": 120_000,
            "realized_capital_gains": 0,
            "noncash_benefits": 0.0,
            "health_insurance_value": 0.0,
            "federal_income_taxes": 8_000,
            "payroll_taxes": 4_000,
            "state_local_income_taxes": 2_000,
        },
    ]


def test_normalize_ipums_cps_asec_extract_reports_missing_raw_columns() -> None:
    raw = ipums_raw_fixture().drop(columns=["HHINCOME"])

    with pytest.raises(ValueError, match="Raw IPUMS CPS ASEC extract missing required columns"):
        normalize_ipums_cps_asec_extract(raw)


def test_normalize_ipums_cps_asec_extract_replaces_niu_codes_with_missing() -> None:
    raw = ipums_raw_fixture()
    raw.loc[0, "HHINCOME"] = 99_999_999

    normalized = normalize_ipums_cps_asec_extract(raw)

    assert pd.isna(normalized.loc[0, "money_income"])


def write_cps_fixture_csv(path: Path) -> None:
    cps_fixture().to_csv(path, index=False)


def write_ipums_raw_fixture_csv(path: Path) -> None:
    ipums_raw_fixture().to_csv(path, index=False)


def test_build_cps_ipums_demo_script_writes_processed_csv(tmp_path: Path) -> None:
    raw_csv = tmp_path / "ipums_cps_asec_extract.csv"
    out_csv = tmp_path / "processed.csv"
    write_cps_fixture_csv(raw_csv)

    result = subprocess.run(
        [
            sys.executable,
            str(repo_root() / "scripts" / "build_cps_ipums_demo.py"),
            "--raw-csv",
            str(raw_csv),
            "--out",
            str(out_csv),
        ],
        cwd=repo_root(),
        check=True,
        capture_output=True,
        text=True,
    )

    output = pd.read_csv(out_csv)

    assert "Wrote 2 CPS/IPUMS median rows" in result.stdout
    assert list(output.columns) == [
        "year",
        "value",
        "series",
        "source",
        "variant",
        "include_capital_gains",
        "include_health_insurance",
        "population",
        "notes",
    ]
    assert output["notes"].unique().tolist() == [
        "Fixture/demo output until built from a real IPUMS extract."
    ]


def test_build_cps_ipums_demo_script_normalizes_ipums_raw_extract(tmp_path: Path) -> None:
    raw_csv = tmp_path / "ipums_cps_asec_raw.csv"
    normalized_csv = tmp_path / "normalized.csv"
    out_csv = tmp_path / "processed.csv"
    write_ipums_raw_fixture_csv(raw_csv)

    result = subprocess.run(
        [
            sys.executable,
            str(repo_root() / "scripts" / "build_cps_ipums_demo.py"),
            "--input-format",
            "ipums",
            "--raw-csv",
            str(raw_csv),
            "--normalized-out",
            str(normalized_csv),
            "--out",
            str(out_csv),
        ],
        cwd=repo_root(),
        check=True,
        capture_output=True,
        text=True,
    )

    normalized = pd.read_csv(normalized_csv)
    output = pd.read_csv(out_csv)

    assert "Wrote 2 normalized CPS/IPUMS rows" in result.stdout
    assert "Wrote 2 CPS/IPUMS median rows" in result.stdout
    assert normalized["year"].tolist() == [2020, 2021]
    assert normalized["household_size"].tolist() == [2, 4]
    assert output["value"].tolist() == [pytest.approx(53_033.008589), 53_000.0]


def test_build_cps_ipums_demo_script_reports_missing_raw_file(tmp_path: Path) -> None:
    missing_raw = tmp_path / "missing.csv"
    out_csv = tmp_path / "processed.csv"

    result = subprocess.run(
        [
            sys.executable,
            str(repo_root() / "scripts" / "build_cps_ipums_demo.py"),
            "--raw-csv",
            str(missing_raw),
            "--out",
            str(out_csv),
        ],
        cwd=repo_root(),
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert f"Expected CPS/IPUMS input file not found: {missing_raw}" in result.stderr
    assert not out_csv.exists()
