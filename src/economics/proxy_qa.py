"""QA helpers for comparing CPS/IPUMS output to public proxy series."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

import pandas as pd

from economics.loaders import CBO_PROXY_VALUE_COL, load_cbo_proxy

CPS_REAL_FILENAME = "cps_ipums_median_adult_equivalent_resources_real.csv"
CBO_PROXY_FILENAME = "cbo_proxy_median_adjusted_income_after_tax_transfer.csv"
FRED_COMPARISON_FILENAMES = (
    "fred_real_median_personal_income.csv",
    "fred_real_median_household_income.csv",
    "fred_real_disposable_personal_income_per_capita.csv",
)


def build_indexed_common_overlap(
    series_frames: Mapping[str, pd.DataFrame],
    *,
    value_col: str = "value",
    year_col: str = "year",
) -> pd.DataFrame:
    """Return tidy indexed rows for the common overlap across all series."""

    if not series_frames:
        raise ValueError("At least one series is required")

    common_years: set[int] | None = None
    normalized_frames: dict[str, pd.DataFrame] = {}
    for series, df in series_frames.items():
        frame = df[[year_col, value_col]].copy()
        frame[year_col] = pd.to_numeric(frame[year_col], errors="coerce")
        frame[value_col] = pd.to_numeric(frame[value_col], errors="coerce")
        frame = frame.dropna(subset=[year_col, value_col]).copy()
        frame[year_col] = frame[year_col].astype(int)
        frame = frame.sort_values(year_col).drop_duplicates(year_col, keep="last")
        normalized_frames[series] = frame

        years = set(frame[year_col])
        common_years = years if common_years is None else common_years.intersection(years)

    if not common_years:
        raise ValueError("No common overlap exists across the supplied series")

    common_start_year = min(common_years)
    common_end_year = max(common_years)
    rows: list[pd.DataFrame] = []
    for series, frame in normalized_frames.items():
        overlap = frame[
            (frame[year_col] >= common_start_year)
            & (frame[year_col] <= common_end_year)
            & frame[year_col].isin(common_years)
        ].copy()
        base_value = float(overlap.loc[overlap[year_col] == common_start_year, value_col].iloc[0])
        overlap["series"] = series
        overlap["index_value"] = overlap[value_col] * 100 / base_value
        overlap["common_start_year"] = common_start_year
        overlap["common_end_year"] = common_end_year
        rows.append(
            overlap.rename(columns={year_col: "year", value_col: "value"})[
                [
                    "year",
                    "series",
                    "value",
                    "index_value",
                    "common_start_year",
                    "common_end_year",
                ]
            ]
        )

    return pd.concat(rows, ignore_index=True).sort_values(["series", "year"]).reset_index(drop=True)


def load_cps_public_proxy_series(processed_dir: str | Path) -> dict[str, pd.DataFrame]:
    """Load CPS real output plus CBO and FRED processed comparison files."""

    processed_dir = Path(processed_dir)
    cps = pd.read_csv(processed_dir / CPS_REAL_FILENAME)
    series_frames = {
        str(cps["series"].iloc[0]): cps[["year", "value"]],
    }

    cbo = load_cbo_proxy(processed_dir / CBO_PROXY_FILENAME)
    series_frames["CBO adjusted income after transfers and taxes"] = cbo[
        ["year", CBO_PROXY_VALUE_COL]
    ].rename(columns={CBO_PROXY_VALUE_COL: "value"})

    for filename in FRED_COMPARISON_FILENAMES:
        df = pd.read_csv(processed_dir / filename)
        series_frames[str(df["series"].iloc[0])] = df[["year", "value"]]

    return series_frames
