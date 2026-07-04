from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest

from economics.cps import (
    CpsVariant,
    build_cps_person_resources,
    diagnose_cps_estimation_attrition,
    estimate_cps_annual_medians,
    normalize_ipums_cps_asec_extract,
    summarize_cps_preflight,
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


def test_normalize_ipums_cps_asec_extract_attaches_household_tax_unit_totals() -> None:
    raw = pd.DataFrame(
        [
            {
                "YEAR": 2021,
                "SERIAL": 1,
                "PERNUM": 1,
                "AGE": 40,
                "ASECWT": 1,
                "NUMPREC": 2,
                "HHINCOME": 80_000,
                "CAPGAIN": 99_999,
                "FEDTAX": 6_000,
                "FICA": 3_000,
                "STATETAX": 1_000,
            },
            {
                "YEAR": 2021,
                "SERIAL": 1,
                "PERNUM": 2,
                "AGE": 10,
                "ASECWT": 1,
                "NUMPREC": 2,
                "HHINCOME": 80_000,
                "CAPGAIN": 99_999,
                "FEDTAX": 99_999_999,
                "FICA": 99_999,
                "STATETAX": 9_999_999,
            },
            {
                "YEAR": 2021,
                "SERIAL": 2,
                "PERNUM": 1,
                "AGE": 40,
                "ASECWT": 1,
                "NUMPREC": 1,
                "HHINCOME": 30_000,
                "CAPGAIN": 99_999,
                "FEDTAX": 2_000,
                "FICA": 1_000,
                "STATETAX": 500,
            },
        ]
    )
    normalized = normalize_ipums_cps_asec_extract(raw)

    rows = build_cps_person_resources(
        normalized,
        CpsVariant(include_capital_gains=False, include_health_insurance=False),
    )

    assert normalized[
        ["serial", "pernum", "federal_income_taxes", "payroll_taxes", "state_local_income_taxes"]
    ].to_dict("records") == [
        {
            "serial": 1,
            "pernum": 1,
            "federal_income_taxes": 6_000.0,
            "payroll_taxes": 3_000.0,
            "state_local_income_taxes": 1_000.0,
        },
        {
            "serial": 1,
            "pernum": 2,
            "federal_income_taxes": 6_000.0,
            "payroll_taxes": 3_000.0,
            "state_local_income_taxes": 1_000.0,
        },
        {
            "serial": 2,
            "pernum": 1,
            "federal_income_taxes": 2_000.0,
            "payroll_taxes": 1_000.0,
            "state_local_income_taxes": 500.0,
        },
    ]
    assert rows[["serial", "pernum", "comprehensive_resources"]].to_dict("records") == [
        {"serial": 1, "pernum": 1, "comprehensive_resources": 70_000.0},
        {"serial": 1, "pernum": 2, "comprehensive_resources": 70_000.0},
        {"serial": 2, "pernum": 1, "comprehensive_resources": 26_500.0},
    ]
    assert rows.loc[rows["serial"] == 1, "equivalized_resources"].tolist() == [
        pytest.approx(49_497.474683),
        pytest.approx(49_497.474683),
    ]


def test_build_cps_person_resources_does_not_resum_repeated_household_components() -> None:
    df = pd.DataFrame(
        [
            {
                "year": 2020,
                "serial": 1,
                "pernum": 1,
                "age": 40,
                "asecwt": 1,
                "household_size": 2,
                "money_income": 80_000,
                "realized_capital_gains": pd.NA,
                "noncash_benefits": 0,
                "health_insurance_value": pd.NA,
                "federal_income_taxes": 10_000,
                "payroll_taxes": 4_000,
                "state_local_income_taxes": 1_000,
            },
            {
                "year": 2020,
                "serial": 1,
                "pernum": 2,
                "age": 10,
                "asecwt": 1,
                "household_size": 2,
                "money_income": 80_000,
                "realized_capital_gains": pd.NA,
                "noncash_benefits": 0,
                "health_insurance_value": pd.NA,
                "federal_income_taxes": 10_000,
                "payroll_taxes": 4_000,
                "state_local_income_taxes": 1_000,
            },
        ]
    )

    rows = build_cps_person_resources(
        df,
        CpsVariant(include_capital_gains=False, include_health_insurance=False),
    )

    assert rows["comprehensive_resources"].tolist() == [65_000.0, 65_000.0]


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


def test_summarize_cps_preflight_reports_missingness_duplicates_and_attrition() -> None:
    df = pd.concat([cps_fixture(), cps_fixture().iloc[[1]]], ignore_index=True)
    df.loc[df["year"] == 2021, "realized_capital_gains"] = pd.NA
    df.loc[df["year"] == 2021, "asecwt"] = 0

    summary = summarize_cps_preflight(df, CpsVariant(include_capital_gains=False))

    assert summary[
        [
            "year",
            "input_rows",
            "duplicate_person_key_rows",
            "bad_weight_rows",
            "missing_realized_capital_gains_rows",
            "population_rows",
            "estimation_rows",
            "estimation_rows_pct",
            "variant",
        ]
    ].to_dict("records") == [
        {
            "year": 2020,
            "input_rows": 3,
            "duplicate_person_key_rows": 2,
            "bad_weight_rows": 0,
            "missing_realized_capital_gains_rows": 0,
            "population_rows": 3,
            "estimation_rows": 3,
            "estimation_rows_pct": 100.0,
            "variant": "all_without_capital_gains_with_health_insurance",
        },
        {
            "year": 2021,
            "input_rows": 1,
            "duplicate_person_key_rows": 0,
            "bad_weight_rows": 1,
            "missing_realized_capital_gains_rows": 1,
            "population_rows": 1,
            "estimation_rows": 0,
            "estimation_rows_pct": 0.0,
            "variant": "all_without_capital_gains_with_health_insurance",
        },
    ]


def test_diagnose_cps_estimation_attrition_segments_dropped_rows() -> None:
    df = pd.concat(
        [
            cps_fixture(),
            pd.DataFrame(
                [
                    {
                        "year": 2020,
                        "serial": 4,
                        "pernum": 1,
                        "age": 12,
                        "asecwt": 1,
                        "household_size": 2,
                        "money_income": 0,
                        "realized_capital_gains": pd.NA,
                        "noncash_benefits": 0,
                        "health_insurance_value": pd.NA,
                        "federal_income_taxes": pd.NA,
                        "payroll_taxes": pd.NA,
                        "state_local_income_taxes": pd.NA,
                    },
                    {
                        "year": 2020,
                        "serial": 5,
                        "pernum": 1,
                        "age": 35,
                        "asecwt": 1,
                        "household_size": 3,
                        "money_income": 150_000,
                        "realized_capital_gains": pd.NA,
                        "noncash_benefits": 0,
                        "health_insurance_value": pd.NA,
                        "federal_income_taxes": pd.NA,
                        "payroll_taxes": pd.NA,
                        "state_local_income_taxes": pd.NA,
                    },
                ]
            ),
        ],
        ignore_index=True,
    )

    diagnostics = diagnose_cps_estimation_attrition(
        df,
        CpsVariant(include_capital_gains=False, include_health_insurance=False),
    )

    assert diagnostics[
        (diagnostics["year"] == 2020)
        & (diagnostics["segment_type"] == "overall")
        & (diagnostics["segment_value"] == "all")
    ].to_dict("records") == [
        {
            "year": 2020,
            "segment_type": "overall",
            "segment_value": "all",
            "population_rows": 4,
            "estimation_rows": 2,
            "dropped_rows": 2,
            "retained_pct": 50.0,
            "bad_weight_rows": 0,
            "bad_household_size_rows": 0,
            "missing_age_rows": 0,
            "missing_required_value_rows": 2,
            "missing_money_income_rows": 0,
            "missing_realized_capital_gains_rows": 2,
            "missing_noncash_benefits_rows": 0,
            "missing_health_insurance_value_rows": 2,
            "missing_federal_income_taxes_rows": 2,
            "missing_payroll_taxes_rows": 2,
            "missing_state_local_income_taxes_rows": 2,
            "variant": "all_without_capital_gains_without_health_insurance",
        },
    ]
    age_rows = diagnostics[
        (diagnostics["year"] == 2020) & (diagnostics["segment_type"] == "age_group")
    ].set_index("segment_value")
    assert age_rows.loc["under_18", "dropped_rows"] == 1
    assert age_rows.loc["25_44", "dropped_rows"] == 1

    income_rows = diagnostics[
        (diagnostics["year"] == 2020)
        & (diagnostics["segment_type"] == "money_income_bucket")
    ].set_index("segment_value")
    assert income_rows.loc["100000_199999", "missing_required_value_rows"] == 1


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
    preflight_csv = tmp_path / "preflight.csv"
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
            "--preflight-out",
            str(preflight_csv),
            "--out",
            str(out_csv),
        ],
        cwd=repo_root(),
        check=True,
        capture_output=True,
        text=True,
    )

    normalized = pd.read_csv(normalized_csv)
    preflight = pd.read_csv(preflight_csv)
    output = pd.read_csv(out_csv)

    assert "Wrote 2 normalized CPS/IPUMS rows" in result.stdout
    assert "Wrote 2 CPS/IPUMS preflight rows" in result.stdout
    assert "Wrote 2 CPS/IPUMS median rows" in result.stdout
    assert normalized["year"].tolist() == [2020, 2021]
    assert normalized["household_size"].tolist() == [2, 4]
    assert preflight["input_rows"].tolist() == [1, 1]
    assert output["value"].tolist() == [pytest.approx(49_497.474683), 53_000.0]
    assert output["variant"].unique().tolist() == [
        "all_without_capital_gains_without_health_insurance"
    ]
    assert output["notes"].unique().tolist() == [
        "Built from a rectangularized IPUMS CPS ASEC extract. The starter bridge "
        "zero-fills noncash benefits and health-insurance value, sums tax-unit "
        "tax components to household totals, and excludes realized capital gains "
        "because CAPGAIN is unavailable after 2008. Review the preflight summary "
        "before interpreting row retention."
    ]


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


def test_diagnose_cps_ipums_attrition_script_writes_diagnostics(tmp_path: Path) -> None:
    raw_csv = tmp_path / "ipums_cps_asec_extract.csv"
    out_csv = tmp_path / "diagnostics.csv"
    df = cps_fixture()
    df.loc[(df["year"] == 2020) & (df["age"] < 18), "federal_income_taxes"] = pd.NA
    df.to_csv(raw_csv, index=False)

    result = subprocess.run(
        [
            sys.executable,
            str(repo_root() / "scripts" / "diagnose_cps_ipums_attrition.py"),
            "--input-csv",
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

    assert "Wrote" in result.stdout
    assert "CPS/IPUMS attrition diagnostic rows" in result.stdout
    assert {
        "overall",
        "age_group",
        "household_size_bucket",
        "money_income_bucket",
    }.issubset(set(output["segment_type"]))
    assert output.loc[
        (output["year"] == 2020)
        & (output["segment_type"] == "overall")
        & (output["segment_value"] == "all"),
        "dropped_rows",
    ].iloc[0] == 1
