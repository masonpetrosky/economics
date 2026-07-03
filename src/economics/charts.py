"""Matplotlib chart helpers for project time series."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.axes import Axes
from matplotlib.figure import Figure


def plot_time_series(
    df: pd.DataFrame,
    value_col: str,
    *,
    year_col: str = "year",
    title: str,
    ylabel: str,
    output_path: str | Path | None = None,
) -> tuple[Figure, Axes]:
    """Plot a single annual time series and optionally save it."""

    ordered = df.sort_values(year_col)
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(ordered[year_col], ordered[value_col], marker="o", linewidth=2)
    ax.set_title(title)
    ax.set_xlabel("Year")
    ax.set_ylabel(ylabel)
    ax.grid(True, axis="y", alpha=0.3)
    ax.yaxis.set_major_formatter(lambda x, pos: f"${x:,.0f}")

    fig.tight_layout()

    if output_path is not None:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(output_path, dpi=200)

    return fig, ax


def plot_multiple_series(
    df: pd.DataFrame,
    *,
    value_col: str = "value",
    series_col: str = "series",
    year_col: str = "year",
    title: str,
    ylabel: str,
    output_path: str | Path | None = None,
) -> tuple[Figure, Axes]:
    """Plot multiple annual time series from a tidy DataFrame."""

    ordered = df.sort_values([series_col, year_col])
    fig, ax = plt.subplots(figsize=(10, 6))
    for series, group in ordered.groupby(series_col, sort=True):
        ax.plot(group[year_col], group[value_col], marker="o", linewidth=2, label=series)

    ax.set_title(title)
    ax.set_xlabel("Year")
    ax.set_ylabel(ylabel)
    ax.grid(True, axis="y", alpha=0.3)
    ax.legend()

    fig.tight_layout()

    if output_path is not None:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(output_path, dpi=200)

    return fig, ax
