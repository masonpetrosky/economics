"""Summary-table helpers."""

from __future__ import annotations

from collections.abc import Mapping

import pandas as pd

from economics.series import summarize_series


def build_summary_table(
    df: pd.DataFrame,
    value_col: str,
    *,
    label: str,
    year_col: str = "year",
) -> pd.DataFrame:
    """Return a long-form summary table for a time series."""

    summary = summarize_series(df, value_col, year_col=year_col)
    rows = [
        {"series": label, "metric": metric, "value": round(float(value), 10)}
        for metric, value in summary.items()
    ]
    return pd.DataFrame(rows)


def build_comparison_summary(
    series_frames: Mapping[str, pd.DataFrame],
    *,
    value_col: str = "value",
    year_col: str = "year",
) -> pd.DataFrame:
    """Return full-span and common-overlap summary rows for multiple series."""

    if not series_frames:
        raise ValueError("At least one series is required")

    common_years: set[int] | None = None
    rows: list[dict[str, float | int | str]] = []
    for series, df in series_frames.items():
        ordered = df.sort_values(year_col)
        summary = summarize_series(ordered, value_col, year_col=year_col)
        rows.append(_summary_row("full_span", series, summary))

        years = set(ordered[year_col].astype(int))
        common_years = years if common_years is None else common_years.intersection(years)

    if not common_years:
        raise ValueError("No common overlap exists across the supplied series")

    common_start = min(common_years)
    common_end = max(common_years)
    for series, df in series_frames.items():
        overlap = df[df[year_col].isin([common_start, common_end])].sort_values(year_col)
        summary = summarize_series(overlap, value_col, year_col=year_col)
        rows.append(_summary_row("common_overlap", series, summary))

    return pd.DataFrame(rows)


def _summary_row(
    summary_period: str,
    series: str,
    summary: dict[str, float],
) -> dict[str, float | int | str]:
    """Convert a summary dictionary to one wide table row."""

    return {
        "summary_period": summary_period,
        "series": series,
        "start_year": int(summary["start_year"]),
        "end_year": int(summary["end_year"]),
        "start_value": round(float(summary["start_value"]), 10),
        "end_value": round(float(summary["end_value"]), 10),
        "cumulative_growth_pct": round(float(summary["cumulative_growth_pct"]), 10),
        "annualized_growth_pct": round(float(summary["annualized_growth_pct"]), 10),
    }
