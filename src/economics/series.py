"""Time-series and weighted-statistic helpers."""

from __future__ import annotations

from collections.abc import Iterable

import pandas as pd


def weighted_median(values: Iterable[float], weights: Iterable[float]) -> float:
    """Calculate a weighted median from values and observation weights."""

    df = pd.DataFrame({"value": list(values), "weight": list(weights)})
    df = df.dropna(subset=["value", "weight"])
    df = df[df["weight"] > 0]

    if df.empty:
        raise ValueError("No positive-weight observations were supplied")

    df = df.sort_values("value").reset_index(drop=True)
    cutoff = df["weight"].sum() / 2
    cumulative_weight = df["weight"].cumsum()

    return float(df.loc[cumulative_weight >= cutoff, "value"].iloc[0])


def real_value(nominal_value: float, price_index: float, base_price_index: float) -> float:
    """Convert a nominal amount to base-period real dollars."""

    if price_index <= 0:
        raise ValueError("price_index must be positive")
    if base_price_index <= 0:
        raise ValueError("base_price_index must be positive")
    return nominal_value * base_price_index / price_index


def add_growth_columns(
    df: pd.DataFrame,
    value_col: str,
    year_col: str = "year",
) -> pd.DataFrame:
    """Add one-year, cumulative, and annualized growth columns."""

    out = df.sort_values(year_col).copy()
    first_value = out[value_col].iloc[0]
    first_year = out[year_col].iloc[0]

    out[f"{value_col}_yoy_pct"] = out[value_col].pct_change() * 100
    out[f"{value_col}_cumulative_pct"] = (out[value_col] / first_value - 1) * 100

    years_elapsed = (out[year_col] - first_year).astype("float").mask(lambda years: years == 0)
    annualized_growth = (
        (out[value_col] / first_value) ** (1 / years_elapsed) - 1
    ) * 100
    out[f"{value_col}_annualized_pct"] = annualized_growth.mask(years_elapsed.isna())

    return out


def summarize_series(
    df: pd.DataFrame,
    value_col: str,
    year_col: str = "year",
) -> dict[str, float]:
    """Return a compact start/end/growth summary for a time series."""

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
