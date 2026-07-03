"""Summary-table helpers."""

from __future__ import annotations

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
