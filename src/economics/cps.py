"""CPS ASEC/IPUMS microdata helpers."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

import pandas as pd

from economics.equivalence import equivalize_resources
from economics.loaders import (
    CPS_IPUMS_REQUIRED_COLUMNS,
    validate_required_columns,
)
from economics.series import weighted_median

DEFAULT_CPS_SERIES = "Median adult-equivalent disposable resources"
DEFAULT_CPS_SOURCE = "CPS ASEC/IPUMS normalized extract"
DEFAULT_CPS_NOTES = "Fixture/demo output until built from a real IPUMS extract."
IPUMS_CPS_SOURCE = "IPUMS CPS ASEC rectangularized extract"
IPUMS_CPS_NOTES_WITHOUT_CAPITAL_GAINS = (
    "Built from a rectangularized IPUMS CPS ASEC extract. The starter bridge "
    "zero-fills noncash benefits and health-insurance value, and this output "
    "excludes realized capital gains because CAPGAIN is unavailable after 2008. "
    "Review the preflight summary before interpreting row retention."
)
IPUMS_CPS_NOTES_WITH_CAPITAL_GAINS = (
    "Built from a rectangularized IPUMS CPS ASEC extract. The starter bridge "
    "zero-fills noncash benefits and health-insurance value. CAPGAIN is only "
    "available through ASEC 2008 in IPUMS CPS."
)
VALID_POPULATIONS = ("all", "adults")
RESOURCE_COMPONENT_COLUMNS = (
    "money_income",
    "realized_capital_gains",
    "noncash_benefits",
    "health_insurance_value",
    "federal_income_taxes",
    "payroll_taxes",
    "state_local_income_taxes",
)
BASE_NUMERIC_COLUMNS = (
    "year",
    "age",
    "asecwt",
    "household_size",
)
CPS_PERSON_KEY_COLUMNS = ("year", "serial", "pernum")
ALWAYS_INCLUDED_RESOURCE_COMPONENT_COLUMNS = (
    "money_income",
    "noncash_benefits",
    "federal_income_taxes",
    "payroll_taxes",
    "state_local_income_taxes",
)
IPUMS_CPS_ASEC_NIU_CODES = {
    "HHINCOME": (99_999_999,),
    "CAPGAIN": (99_999,),
    "FEDTAX": (99_999_999,),
    "FICA": (99_999,),
    "STATETAX": (9_999_999,),
}


@dataclass(frozen=True)
class IpumsCpsAsecMapping:
    """Column mapping from a rectangularized IPUMS CPS ASEC extract."""

    survey_year: str = "YEAR"
    serial: str = "SERIAL"
    pernum: str = "PERNUM"
    age: str = "AGE"
    asecwt: str = "ASECWT"
    household_size: str = "NUMPREC"
    money_income: str = "HHINCOME"
    realized_capital_gains: str = "CAPGAIN"
    federal_income_taxes: str = "FEDTAX"
    payroll_taxes: str = "FICA"
    state_local_income_taxes: str = "STATETAX"
    noncash_benefits: str | None = None
    health_insurance_value: str | None = None
    income_year_offset: int = -1

    @property
    def required_columns(self) -> tuple[str, ...]:
        """Return the raw columns needed for this mapping."""

        columns = (
            self.survey_year,
            self.serial,
            self.pernum,
            self.age,
            self.asecwt,
            self.household_size,
            self.money_income,
            self.realized_capital_gains,
            self.federal_income_taxes,
            self.payroll_taxes,
            self.state_local_income_taxes,
            self.noncash_benefits,
            self.health_insurance_value,
        )
        return tuple(column for column in columns if column is not None)


DEFAULT_IPUMS_CPS_ASEC_MAPPING = IpumsCpsAsecMapping()


@dataclass(frozen=True)
class CpsVariant:
    """Sensitivity switches for normalized CPS/IPUMS estimation."""

    include_capital_gains: bool = True
    include_health_insurance: bool = True
    population: str = "all"
    adult_age_min: int = 18

    def __post_init__(self) -> None:
        """Validate variant values at construction time."""

        if self.population not in VALID_POPULATIONS:
            raise ValueError("population must be one of: all, adults")
        if self.adult_age_min <= 0:
            raise ValueError("adult_age_min must be positive")

    @property
    def label(self) -> str:
        """Return a stable variant label for processed output."""

        gains = "with_capital_gains" if self.include_capital_gains else "without_capital_gains"
        health = (
            "with_health_insurance"
            if self.include_health_insurance
            else "without_health_insurance"
        )
        return f"{self.population}_{gains}_{health}"


DEFAULT_CPS_VARIANT = CpsVariant()


def _read_ipums_numeric_column(df: pd.DataFrame, column: str) -> pd.Series:
    values = pd.to_numeric(df[column], errors="coerce")
    niu_codes = IPUMS_CPS_ASEC_NIU_CODES.get(column.upper(), ())
    if niu_codes:
        values = values.mask(values.isin(niu_codes))
    return values


def _read_optional_ipums_numeric_column(
    df: pd.DataFrame,
    column: str | None,
) -> pd.Series:
    if column is None:
        return pd.Series(0.0, index=df.index)
    return _read_ipums_numeric_column(df, column)


def _required_numeric_columns(variant: CpsVariant) -> tuple[str, ...]:
    columns = [*BASE_NUMERIC_COLUMNS, *ALWAYS_INCLUDED_RESOURCE_COMPONENT_COLUMNS]
    if variant.include_capital_gains:
        columns.append("realized_capital_gains")
    if variant.include_health_insurance:
        columns.append("health_insurance_value")
    return tuple(columns)


def _observed_years(df: pd.DataFrame) -> set[int]:
    return set(df["year"].dropna().astype(int).unique())


def _format_years(years: set[int]) -> str:
    return ", ".join(str(year) for year in sorted(years))


def _raise_if_years_lost(
    before_years: set[int],
    after_years: set[int],
    *,
    empty_message: str,
    partial_message: str,
) -> None:
    lost_years = before_years - after_years
    if not lost_years:
        return

    years = _format_years(lost_years)
    if after_years:
        raise ValueError(f"{partial_message}: {years}")
    raise ValueError(f"{empty_message}: {years}")


def _raise_if_duplicate_person_rows(df: pd.DataFrame) -> None:
    duplicate_mask = df.duplicated(subset=CPS_PERSON_KEY_COLUMNS, keep=False)
    if not duplicate_mask.any():
        return

    duplicate_keys = (
        df.loc[duplicate_mask, list(CPS_PERSON_KEY_COLUMNS)]
        .drop_duplicates()
        .sort_values(list(CPS_PERSON_KEY_COLUMNS))
    )
    key_details = "; ".join(
        f"year={row.year}, serial={row.serial}, pernum={row.pernum}"
        for row in duplicate_keys.itertuples(index=False)
    )
    raise ValueError(f"Duplicate CPS person rows for key(s): {key_details}")


def _empty_year_summary(df: pd.DataFrame) -> pd.DataFrame:
    years = (
        pd.to_numeric(df["year"], errors="coerce")
        .dropna()
        .astype(int)
        .sort_values()
        .unique()
    )
    return pd.DataFrame({"year": years})


def validate_cps_columns(
    df: pd.DataFrame,
    source_label: str = "CPS/IPUMS input",
    required_columns: Iterable[str] = CPS_IPUMS_REQUIRED_COLUMNS,
) -> None:
    """Raise a clear error if normalized CPS/IPUMS input lacks required columns."""

    validate_required_columns(df, required_columns, source_label)


def normalize_ipums_cps_asec_extract(
    df: pd.DataFrame,
    mapping: IpumsCpsAsecMapping = DEFAULT_IPUMS_CPS_ASEC_MAPPING,
    source_label: str = "Raw IPUMS CPS ASEC extract",
) -> pd.DataFrame:
    """Normalize a rectangularized IPUMS CPS ASEC extract into the project contract."""

    validate_required_columns(df, mapping.required_columns, source_label)
    survey_year = _read_ipums_numeric_column(df, mapping.survey_year)
    out = pd.DataFrame(
        {
            "year": survey_year + mapping.income_year_offset,
            "serial": _read_ipums_numeric_column(df, mapping.serial),
            "pernum": _read_ipums_numeric_column(df, mapping.pernum),
            "age": _read_ipums_numeric_column(df, mapping.age),
            "asecwt": _read_ipums_numeric_column(df, mapping.asecwt),
            "household_size": _read_ipums_numeric_column(df, mapping.household_size),
            "money_income": _read_ipums_numeric_column(df, mapping.money_income),
            "realized_capital_gains": _read_ipums_numeric_column(
                df, mapping.realized_capital_gains
            ),
            "noncash_benefits": _read_optional_ipums_numeric_column(
                df, mapping.noncash_benefits
            ),
            "health_insurance_value": _read_optional_ipums_numeric_column(
                df, mapping.health_insurance_value
            ),
            "federal_income_taxes": _read_ipums_numeric_column(
                df, mapping.federal_income_taxes
            ),
            "payroll_taxes": _read_ipums_numeric_column(df, mapping.payroll_taxes),
            "state_local_income_taxes": _read_ipums_numeric_column(
                df, mapping.state_local_income_taxes
            ),
        }
    )
    validate_cps_columns(out, source_label="Normalized IPUMS CPS ASEC extract")
    return out[list(CPS_IPUMS_REQUIRED_COLUMNS)].reset_index(drop=True)


def summarize_cps_preflight(
    df: pd.DataFrame,
    variant: CpsVariant = DEFAULT_CPS_VARIANT,
) -> pd.DataFrame:
    """Return per-year row, missingness, duplicate, and filter-attrition checks."""

    validate_cps_columns(df)
    work = df.copy()
    work["year"] = pd.to_numeric(work["year"], errors="coerce")
    work = work.dropna(subset=["year"])
    if work.empty:
        raise ValueError("No CPS rows contain a valid year")
    work["year"] = work["year"].astype(int)

    for column in (*BASE_NUMERIC_COLUMNS, *RESOURCE_COMPONENT_COLUMNS):
        work[column] = pd.to_numeric(work[column], errors="coerce")

    summary = _empty_year_summary(work)
    yearly = work.groupby("year", sort=True)
    summary = summary.merge(yearly.size().rename("input_rows"), on="year", how="left")

    duplicate_mask = work.duplicated(subset=CPS_PERSON_KEY_COLUMNS, keep=False)
    duplicate_rows = duplicate_mask.groupby(work["year"]).sum().rename("duplicate_person_key_rows")
    summary = summary.merge(duplicate_rows, on="year", how="left")

    bad_weight = ((work["asecwt"].isna()) | (work["asecwt"] <= 0)).groupby(work["year"]).sum()
    bad_hh_size = (
        ((work["household_size"].isna()) | (work["household_size"] <= 0))
        .groupby(work["year"])
        .sum()
    )
    summary = summary.merge(bad_weight.rename("bad_weight_rows"), on="year", how="left")
    summary = summary.merge(bad_hh_size.rename("bad_household_size_rows"), on="year", how="left")

    for column in RESOURCE_COMPONENT_COLUMNS:
        missing = work[column].isna().groupby(work["year"]).sum()
        summary = summary.merge(missing.rename(f"missing_{column}_rows"), on="year", how="left")

    if variant.population == "adults":
        population = work[work["age"] >= variant.adult_age_min]
    else:
        population = work
    population_rows = population.groupby("year").size().rename("population_rows")
    summary = summary.merge(population_rows, on="year", how="left")

    required_numeric_columns = _required_numeric_columns(variant)
    estimation = work.dropna(subset=required_numeric_columns)
    estimation = estimation[(estimation["asecwt"] > 0) & (estimation["household_size"] > 0)]
    if variant.population == "adults":
        estimation = estimation[estimation["age"] >= variant.adult_age_min]

    estimation_rows = estimation.groupby("year").size().rename("estimation_rows")
    summary = summary.merge(estimation_rows, on="year", how="left")
    summary = summary.fillna(0)
    integer_columns = [column for column in summary.columns if column.endswith("_rows")]
    summary[integer_columns] = summary[integer_columns].astype(int)
    summary["input_rows"] = summary["input_rows"].astype(int)
    summary["estimation_rows_pct"] = (
        summary["estimation_rows"] / summary["population_rows"] * 100
    ).round(2)
    summary["variant"] = variant.label
    return summary.sort_values("year").reset_index(drop=True)


def build_cps_person_resources(
    df: pd.DataFrame,
    variant: CpsVariant = DEFAULT_CPS_VARIANT,
) -> pd.DataFrame:
    """Return person rows with comprehensive and equivalized resources."""

    validate_cps_columns(df)
    _raise_if_duplicate_person_rows(df)
    work = df.copy()
    required_numeric_columns = _required_numeric_columns(variant)
    work["year"] = pd.to_numeric(work["year"], errors="coerce")
    input_years = _observed_years(work)

    for column in required_numeric_columns:
        work[column] = pd.to_numeric(work[column], errors="coerce")

    work = work.dropna(subset=required_numeric_columns)
    work = work[(work["asecwt"] > 0) & (work["household_size"] > 0)]
    _raise_if_years_lost(
        input_years,
        _observed_years(work),
        empty_message=(
            "No CPS observations remain after filtering invalid weights and household sizes "
            "or required component values"
        ),
        partial_message=(
            "No CPS observations remain for CPS year(s) after filtering invalid weights "
            "and household sizes or required component values"
        ),
    )
    if work.empty:
        raise ValueError(
            "No CPS observations remain after filtering invalid weights and household sizes "
            "or required component values"
        )

    if variant.population == "adults":
        pre_population_years = _observed_years(work)
        work = work[work["age"] >= variant.adult_age_min]
        _raise_if_years_lost(
            pre_population_years,
            _observed_years(work),
            empty_message="No CPS observations remain after applying population filter: adults",
            partial_message=(
                "No CPS observations remain for CPS year(s) after applying population "
                "filter: adults"
            ),
        )
        if work.empty:
            raise ValueError("No CPS observations remain after applying population filter: adults")

    capital_gains = work["realized_capital_gains"] if variant.include_capital_gains else 0.0
    health_insurance = work["health_insurance_value"] if variant.include_health_insurance else 0.0
    taxes = (
        work["federal_income_taxes"]
        + work["payroll_taxes"]
        + work["state_local_income_taxes"]
    )

    out = work.copy()
    out["year"] = out["year"].astype(int)
    out["comprehensive_resources"] = (
        work["money_income"] + capital_gains + work["noncash_benefits"] + health_insurance - taxes
    )
    out["equivalized_resources"] = [
        equivalize_resources(resources, household_size)
        for resources, household_size in zip(
            out["comprehensive_resources"],
            out["household_size"],
            strict=True,
        )
    ]
    return out.reset_index(drop=True)


def estimate_cps_annual_medians(
    df: pd.DataFrame,
    variant: CpsVariant = DEFAULT_CPS_VARIANT,
    series: str = DEFAULT_CPS_SERIES,
    source: str = DEFAULT_CPS_SOURCE,
    notes: str = DEFAULT_CPS_NOTES,
) -> pd.DataFrame:
    """Estimate person-weighted annual medians from normalized CPS/IPUMS rows."""

    person_rows = build_cps_person_resources(df, variant)
    rows: list[dict[str, float | int | str | bool]] = []
    for year, year_rows in person_rows.groupby("year", sort=True):
        rows.append(
            {
                "year": int(year),
                "value": weighted_median(
                    year_rows["equivalized_resources"],
                    year_rows["asecwt"],
                ),
                "series": series,
                "source": source,
                "variant": variant.label,
                "include_capital_gains": variant.include_capital_gains,
                "include_health_insurance": variant.include_health_insurance,
                "population": variant.population,
                "notes": notes,
            }
        )

    if not rows:
        raise ValueError("No annual CPS medians could be estimated")

    return pd.DataFrame(rows).sort_values("year").reset_index(drop=True)
