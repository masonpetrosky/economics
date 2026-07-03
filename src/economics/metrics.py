"""Core metric helpers for the economics project.

These functions are intentionally small and boring. The first version of this
project should make the methodology easy to audit before becoming clever.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import sqrt
from pathlib import Path
from typing import Iterable

import pandas as pd


@dataclass(frozen=True)
class ResourceComponents:
    """Components of a broad disposable-resource measure.

    The default values make it easy to construct partial estimates while the
    project is still moving from aggregate public proxies toward microdata.

    Amounts should be expressed in the same dollar year before combining.
    """

    money_income: float = 0.0
    realized_capital_gains: float = 0.0
    noncash_benefits: float = 0.0
    health_insurance_value: float = 0.0
    federal_income_taxes: float = 0.0
    payroll_taxes: float = 0.0
    state_local_income_taxes: float = 0.0

    def comprehensive_disposable_resources(self) -> float:
        """Return broad resources after taxes.

        This is a conceptual helper, not a final official definition.
        Health-insurance valuation and capital gains should eventually be
        included as sensitivity toggles.
        """

        resources = (
            self.money_income
            + self.realized_capital_gains
            + self.noncash_benefits
            + self.health_insurance_value
        )
        taxes = (
            self.federal_income_taxes
            + self.payroll_taxes
            + self.state_local_income_taxes
        )
        return resources - taxes


def square_root_equivalence_scale(household_size: float) -> float:
    """Return the square-root equivalence scale for a household.

    A two-person household is assumed to need more resources than a one-person
    household, but less than twice as much, because housing and other costs are
    partly shared.

    Parameters
    ----------
    household_size:
        Number of people in the household or resource unit. Must be positive.
    """

    if household_size <= 0:
        raise ValueError("household_size must be positive")
    return sqrt(household_size)


def equivalize_resources(resources: float, household_size: float) -> float:
    """Adjust household resources for household size."""

    return resources / square_root_equivalence_scale(household_size)


def weighted_median(
    values: Iterable[float],
    weights: Iterable[float],
) -> float:
    """Calculate a weighted median.

    This is the key statistic for the eventual microdata build. For each year,
    calculate equivalized resources for every person, weight by the person
    weight, and take the weighted median.
    """

    df = pd.DataFrame({"value": list(values), "weight": list(weights)})
    df = df.dropna(subset=["value", "weight"])
    df = df[df["weight"] > 0]

    if df.empty:
        raise ValueError("No positive-weight observations were supplied")

    df = df.sort_values("value").reset_index(drop=True)
    cutoff = df["weight"].sum() / 2
    cumulative_weight = df["weight"].cumsum()

    return float(df.loc[cumulative_weight >= cutoff, "value"].iloc[0])


def add_growth_columns(
    df: pd.DataFrame,
    value_col: str,
    year_col: str = "year",
) -> pd.DataFrame:
    """Add one-year, cumulative, and annualized growth columns.

    Returns a copy of the input DataFrame.
    """

    out = df.sort_values(year_col).copy()
    first_value = out[value_col].iloc[0]
    first_year = out[year_col].iloc[0]

    out[f"{value_col}_yoy_pct"] = out[value_col].pct_change() * 100
    out[f"{value_col}_cumulative_pct"] = (out[value_col] / first_value - 1) * 100

    years_elapsed = out[year_col] - first_year
    out[f"{value_col}_annualized_pct"] = (
        (out[value_col] / first_value) ** (1 / years_elapsed.replace(0, pd.NA)) - 1
    ) * 100

    return out


def load_cbo_proxy(path: str | Path) -> pd.DataFrame:
    """Load the starter CBO proxy CSV.

    Expected columns:
    - year
    - median_adjusted_income_after_transfers_taxes_2022_dollars
    """

    path = Path(path)
    df = pd.read_csv(path)

    required = {
        "year",
        "median_adjusted_income_after_transfers_taxes_2022_dollars",
    }
    missing = required.difference(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    return df.sort_values("year").reset_index(drop=True)


def summarize_series(
    df: pd.DataFrame,
    value_col: str,
    year_col: str = "year",
) -> dict[str, float]:
    """Return a compact summary of a time series."""

    ordered = df.sort_values(year_col)
    first = ordered.iloc[0]
    last = ordered.iloc[-1]

    years = float(last[year_col] - first[year_col])
    cumulative_growth = float(last[value_col] / first[value_col] - 1)

    if years <= 0:
        annualized_growth = float("nan")
    else:
        annualized_growth = float((last[value_col] / first[value_col]) ** (1 / years) - 1)

    return {
        "start_year": int(first[year_col]),
        "end_year": int(last[year_col]),
        "start_value": float(first[value_col]),
        "end_value": float(last[value_col]),
        "cumulative_growth_pct": cumulative_growth * 100,
        "annualized_growth_pct": annualized_growth * 100,
    }
