"""CPS ASEC/IPUMS microdata helpers."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

import pandas as pd

from economics.equivalence import equivalize_resources
from economics.loaders import CPS_IPUMS_REQUIRED_COLUMNS, validate_required_columns
from economics.series import weighted_median

DEFAULT_CPS_SERIES = "Median adult-equivalent disposable resources"
DEFAULT_CPS_SOURCE = "CPS ASEC/IPUMS normalized extract"
DEFAULT_CPS_NOTES = "Fixture/demo output until built from a real IPUMS extract."
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
NUMERIC_COLUMNS = (
    "year",
    "age",
    "asecwt",
    "household_size",
    *RESOURCE_COMPONENT_COLUMNS,
)


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


def validate_cps_columns(
    df: pd.DataFrame,
    source_label: str = "CPS/IPUMS input",
    required_columns: Iterable[str] = CPS_IPUMS_REQUIRED_COLUMNS,
) -> None:
    """Raise a clear error if normalized CPS/IPUMS input lacks required columns."""

    validate_required_columns(df, required_columns, source_label)


def build_cps_person_resources(
    df: pd.DataFrame,
    variant: CpsVariant = DEFAULT_CPS_VARIANT,
) -> pd.DataFrame:
    """Return person rows with comprehensive and equivalized resources."""

    validate_cps_columns(df)
    work = df.copy()
    for column in NUMERIC_COLUMNS:
        work[column] = pd.to_numeric(work[column], errors="coerce")

    work = work.dropna(subset=NUMERIC_COLUMNS)
    work = work[(work["asecwt"] > 0) & (work["household_size"] > 0)]
    if work.empty:
        raise ValueError(
            "No CPS observations remain after filtering invalid weights and household sizes"
        )

    if variant.population == "adults":
        work = work[work["age"] >= variant.adult_age_min]
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
