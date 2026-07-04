"""CSV loaders for public proxy and comparison series."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

CBO_PROXY_VALUE_COL = "median_adjusted_income_after_transfers_taxes_2022_dollars"
CPS_IPUMS_REQUIRED_COLUMNS = (
    "year",
    "serial",
    "pernum",
    "age",
    "asecwt",
    "household_size",
    "money_income",
    "realized_capital_gains",
    "noncash_benefits",
    "health_insurance_value",
    "federal_income_taxes",
    "payroll_taxes",
    "state_local_income_taxes",
)
IPUMS_CPS_ASEC_RAW_REQUIRED_COLUMNS = (
    "YEAR",
    "SERIAL",
    "PERNUM",
    "AGE",
    "ASECWT",
    "NUMPREC",
    "HHINCOME",
    "CAPGAIN",
    "FEDTAX",
    "FICA",
    "STATETAX",
)


@dataclass(frozen=True)
class SourceFileSpec:
    """Manual source-file contract for a public data series."""

    file_name: str
    required_columns: tuple[str, ...]
    description: str


RAW_SOURCE_FILE_SPECS: dict[str, SourceFileSpec] = {
    "cbo_distribution_household_income_2022": SourceFileSpec(
        file_name="61911-additional-data-for-researchers.zip",
        required_columns=("year", "adj_inc_after_transfers_taxes"),
        description=(
            "CBO researchers ZIP containing adjusted household income after transfers "
            "and federal taxes."
        ),
    ),
    "ipums_cps_asec_extract": SourceFileSpec(
        file_name="ipums_cps_asec_extract.csv",
        required_columns=CPS_IPUMS_REQUIRED_COLUMNS,
        description=(
            "Normalized CPS ASEC/IPUMS person-level extract for custom "
            "adult-equivalent disposable-resource estimates."
        ),
    ),
    "ipums_cps_asec_raw_extract": SourceFileSpec(
        file_name="ipums_cps_asec_raw.csv",
        required_columns=IPUMS_CPS_ASEC_RAW_REQUIRED_COLUMNS,
        description=(
            "Rectangularized IPUMS CPS ASEC extract with official uppercase IPUMS "
            "columns that can be normalized into the project CPS contract."
        ),
    ),
    "fred_real_median_personal_income": SourceFileSpec(
        file_name="fred_real_median_personal_income.csv",
        required_columns=("year", "value"),
        description=(
            "FRED/Census real median personal income comparison series. The FRED "
            "builder also accepts observation_date,MEPAINUSA672N graph exports."
        ),
    ),
    "fred_real_median_household_income": SourceFileSpec(
        file_name="fred_real_median_household_income.csv",
        required_columns=("year", "value"),
        description=(
            "FRED/Census real median household income comparison series. The FRED "
            "builder also accepts observation_date,MEHOINUSA672N graph exports."
        ),
    ),
    "fred_real_disposable_personal_income_per_capita": SourceFileSpec(
        file_name="fred_real_disposable_personal_income_per_capita.csv",
        required_columns=("year", "value"),
        description=(
            "FRED/BEA real disposable personal income per capita comparison series. "
            "The FRED builder also accepts observation_date,A229RX0 graph exports."
        ),
    ),
}


def validate_required_columns(
    df: pd.DataFrame,
    required_columns: Iterable[str],
    source_label: str,
) -> None:
    """Raise a clear error if a DataFrame lacks required columns."""

    missing = sorted(set(required_columns).difference(df.columns))
    if missing:
        raise ValueError(f"{source_label} missing required columns: {missing}")


def load_cbo_proxy(path: str | Path) -> pd.DataFrame:
    """Load the starter CBO proxy CSV and sort it by year."""

    path = Path(path)
    df = pd.read_csv(path)
    validate_required_columns(df, ["year", CBO_PROXY_VALUE_COL], str(path))
    return df.sort_values("year").reset_index(drop=True)


def load_comparison_series(
    path: str | Path,
    value_col: str = "value",
    year_col: str = "year",
    series_name: str | None = None,
) -> pd.DataFrame:
    """Load a simple annual comparison series as year/value/series columns."""

    path = Path(path)
    df = pd.read_csv(path)
    validate_required_columns(df, [year_col, value_col], str(path))

    out = df[[year_col, value_col]].rename(columns={year_col: "year", value_col: "value"})
    if series_name is not None:
        out["series"] = series_name
    return out.sort_values("year").reset_index(drop=True)
