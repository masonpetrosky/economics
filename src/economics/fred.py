"""FRED raw-source ingestion helpers for public comparison series."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd


@dataclass(frozen=True)
class FredSeriesSpec:
    """Source contract and metadata for one FRED comparison series."""

    key: str
    fred_id: str
    series: str
    source: str
    notes: str
    raw_file_name: str
    processed_file_name: str
    frequency: str = "annual"
    min_observations_per_year: int = 1


FRED_SERIES: dict[str, FredSeriesSpec] = {
    "real_median_personal_income": FredSeriesSpec(
        key="real_median_personal_income",
        fred_id="MEPAINUSA672N",
        series="Real median personal income",
        source="FRED/Census MEPAINUSA672N",
        notes="2024 C-CPI-U dollars; annual; not seasonally adjusted.",
        raw_file_name="fred_real_median_personal_income.csv",
        processed_file_name="fred_real_median_personal_income.csv",
    ),
    "real_median_household_income": FredSeriesSpec(
        key="real_median_household_income",
        fred_id="MEHOINUSA672N",
        series="Real median household income",
        source="FRED/Census MEHOINUSA672N",
        notes="2024 C-CPI-U dollars; annual; not seasonally adjusted.",
        raw_file_name="fred_real_median_household_income.csv",
        processed_file_name="fred_real_median_household_income.csv",
    ),
    "real_disposable_personal_income_per_capita": FredSeriesSpec(
        key="real_disposable_personal_income_per_capita",
        fred_id="A229RX0",
        series="Real disposable personal income per capita",
        source="FRED/BEA A229RX0",
        notes=(
            "Chained 2017 dollars; monthly seasonally adjusted annual rate; "
            "annual value is the calendar-year mean of complete years."
        ),
        raw_file_name="fred_real_disposable_personal_income_per_capita.csv",
        processed_file_name="fred_real_disposable_personal_income_per_capita.csv",
        frequency="monthly",
        min_observations_per_year=12,
    ),
}


def build_fred_series(raw_csv_path: str | Path, spec: FredSeriesSpec) -> pd.DataFrame:
    """Normalize one FRED raw CSV into the project comparison schema."""

    raw_csv_path = Path(raw_csv_path)
    raw = pd.read_csv(raw_csv_path, na_values=["."])
    annual = _normalize_raw_series(raw, spec, str(raw_csv_path))

    annual["series_id"] = spec.fred_id
    annual["series"] = spec.series
    annual["source"] = spec.source
    annual["notes"] = spec.notes
    return annual[["year", "value", "series_id", "series", "source", "notes"]]


def build_all_fred_series(
    raw_dir: str | Path,
    processed_dir: str | Path,
) -> dict[str, Path]:
    """Build every configured FRED comparison series and write processed CSVs."""

    raw_dir = Path(raw_dir)
    processed_dir = Path(processed_dir)
    processed_dir.mkdir(parents=True, exist_ok=True)

    outputs: dict[str, Path] = {}
    for key, spec in FRED_SERIES.items():
        df = build_fred_series(raw_dir / spec.raw_file_name, spec)
        output_path = processed_dir / spec.processed_file_name
        df.to_csv(output_path, index=False)
        outputs[key] = output_path
    return outputs


def _normalize_raw_series(
    raw: pd.DataFrame,
    spec: FredSeriesSpec,
    source_label: str,
) -> pd.DataFrame:
    """Extract year/value pairs from either project-shaped or FRED-shaped CSVs."""

    if {"year", "value"}.issubset(raw.columns):
        observations = raw[["year", "value"]].copy()
        observations["year"] = pd.to_numeric(observations["year"], errors="coerce")
        observations["value"] = pd.to_numeric(observations["value"], errors="coerce")
        observations["month"] = pd.NA
        already_annual = True
    else:
        date_col = _find_column(raw, ["observation_date", "DATE", "date"])
        value_col = _find_column(raw, [spec.fred_id, "value"])
        if date_col is None or value_col is None:
            raise ValueError(
                f"{source_label} expected either columns ['year', 'value'] or "
                f"a date column plus one of [{spec.fred_id!r}, 'value']"
            )
        dates = pd.to_datetime(raw[date_col], errors="coerce")
        observations = pd.DataFrame(
            {
                "year": dates.dt.year,
                "month": dates.dt.month,
                "value": pd.to_numeric(raw[value_col], errors="coerce"),
            }
        )
        already_annual = False

    observations = observations.dropna(subset=["year", "value"]).copy()
    observations["year"] = observations["year"].astype(int)

    if spec.frequency == "monthly" and not already_annual:
        monthly = observations.groupby(["year", "month"], as_index=False).agg(
            value=("value", "mean")
        )
        grouped = monthly.groupby("year", as_index=False).agg(
            value=("value", "mean"),
            observations=("month", "nunique"),
        )
        grouped = grouped[grouped["observations"] >= spec.min_observations_per_year]
        annual = grouped[["year", "value"]]
    else:
        annual = observations.sort_values("year").drop_duplicates("year", keep="last")

    return annual.sort_values("year").reset_index(drop=True)


def _find_column(df: pd.DataFrame, candidates: list[str]) -> str | None:
    """Return the first matching column name, case-insensitive where possible."""

    exact = [candidate for candidate in candidates if candidate in df.columns]
    if exact:
        return exact[0]

    columns_by_lower = {column.lower(): column for column in df.columns}
    for candidate in candidates:
        match = columns_by_lower.get(candidate.lower())
        if match is not None:
            return match
    return None
