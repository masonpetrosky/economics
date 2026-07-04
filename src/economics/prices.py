"""Annual price-index helpers for real-dollar conversion."""

from __future__ import annotations

import pandas as pd

from economics.loaders import validate_required_columns
from economics.series import real_value

PRICE_INDEX_REQUIRED_COLUMNS = ("year", "price_index")
DEFAULT_REAL_BASE_YEAR = 2024


def validate_annual_price_index(
    df: pd.DataFrame,
    source_label: str = "annual price index",
) -> pd.DataFrame:
    """Validate and normalize an annual price-index table."""

    validate_required_columns(df, PRICE_INDEX_REQUIRED_COLUMNS, source_label)

    out = df[list(PRICE_INDEX_REQUIRED_COLUMNS)].copy()
    out["year"] = pd.to_numeric(out["year"], errors="coerce")
    out["price_index"] = pd.to_numeric(out["price_index"], errors="coerce")

    if out["year"].isna().any():
        raise ValueError(f"{source_label} has nonnumeric year values")
    if out["price_index"].isna().any():
        raise ValueError(f"{source_label} has nonnumeric price_index values")

    out["year"] = out["year"].astype(int)

    duplicate_years = sorted(out.loc[out.duplicated("year", keep=False), "year"].unique())
    if duplicate_years:
        raise ValueError(
            f"{source_label} has duplicate years: "
            + ", ".join(str(year) for year in duplicate_years)
        )

    nonpositive_years = sorted(out.loc[out["price_index"] <= 0, "year"].unique())
    if nonpositive_years:
        raise ValueError(
            f"{source_label} has nonpositive price_index values for years: "
            + ", ".join(str(year) for year in nonpositive_years)
        )

    return out.sort_values("year").reset_index(drop=True)


def convert_nominal_series_to_real(
    nominal_df: pd.DataFrame,
    price_index_df: pd.DataFrame,
    *,
    base_year: int = DEFAULT_REAL_BASE_YEAR,
    value_col: str = "value",
    year_col: str = "year",
) -> pd.DataFrame:
    """Convert a nominal annual series to real dollars using an annual price index."""

    validate_required_columns(nominal_df, [year_col, value_col], "nominal series")
    work = nominal_df.copy()
    work[year_col] = pd.to_numeric(work[year_col], errors="coerce")
    work[value_col] = pd.to_numeric(work[value_col], errors="coerce")

    if work[year_col].isna().any():
        raise ValueError("nominal series has nonnumeric year values")
    if work[value_col].isna().any():
        raise ValueError("nominal series has nonnumeric value values")

    work[year_col] = work[year_col].astype(int)
    prices = validate_annual_price_index(price_index_df)
    price_years = set(prices["year"])
    nominal_years = set(work[year_col])

    missing_years = sorted(nominal_years.difference(price_years))
    if missing_years:
        raise ValueError(
            "price index missing years required by nominal series: "
            + ", ".join(str(year) for year in missing_years)
        )

    base_rows = prices.loc[prices["year"] == base_year, "price_index"]
    if base_rows.empty:
        raise ValueError(f"price index missing requested base year: {base_year}")

    base_price_index = float(base_rows.iloc[0])
    merged = work.merge(prices, left_on=year_col, right_on="year", how="left")
    merged["nominal_value"] = merged[value_col].astype(float)
    merged["value"] = [
        real_value(
            nominal_value=float(nominal_value),
            price_index=float(price_index),
            base_price_index=base_price_index,
        )
        for nominal_value, price_index in zip(
            merged["nominal_value"],
            merged["price_index"],
            strict=True,
        )
    ]
    merged["real_base_year"] = int(base_year)

    metadata_cols = [
        column
        for column in nominal_df.columns
        if column not in {year_col, value_col}
    ]
    return merged[
        ["year", "value", "nominal_value", "price_index", "real_base_year", *metadata_cols]
    ].sort_values("year").reset_index(drop=True)
