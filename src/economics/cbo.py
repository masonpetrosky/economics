"""CBO raw-source ingestion helpers."""

from __future__ import annotations

from pathlib import Path
from zipfile import BadZipFile, ZipFile

import pandas as pd

from economics.loaders import CBO_PROXY_VALUE_COL, validate_required_columns

CBO_RESEARCHERS_ZIP_FILENAME = "61911-additional-data-for-researchers.zip"
CBO_RESEARCHERS_ZIP_MEMBER = (
    "61911-additional-data-for-researchers/"
    "CBO_distribution_household_income_2022_data/"
    "households_ranked_by_inc_after_trans_tax_table_04_median_household_income_1979_2022.csv"
)
CBO_RESEARCHERS_SOURCE = (
    "CBO Distribution of Household Income, 2022 Additional Data for Researchers"
)
CBO_PROXY_NOTES = (
    "Median adjusted household income after transfers and federal taxes; "
    "2022 dollars; households ranked by income after transfers and taxes."
)


def build_cbo_proxy_from_researchers_zip(raw_zip_path: str | Path) -> pd.DataFrame:
    """Build the processed CBO proxy series from the official researchers ZIP."""

    raw_zip_path = Path(raw_zip_path)
    try:
        with ZipFile(raw_zip_path) as archive:
            if CBO_RESEARCHERS_ZIP_MEMBER not in archive.namelist():
                raise ValueError(
                    f"{raw_zip_path} does not contain expected CBO member: "
                    f"{CBO_RESEARCHERS_ZIP_MEMBER}"
                )
            with archive.open(CBO_RESEARCHERS_ZIP_MEMBER) as handle:
                raw = pd.read_csv(handle)
    except BadZipFile as exc:
        raise ValueError(f"{raw_zip_path} is not a readable ZIP file") from exc

    validate_required_columns(
        raw,
        ["year", "adj_inc_after_transfers_taxes"],
        CBO_RESEARCHERS_ZIP_MEMBER,
    )

    out = raw[["year", "adj_inc_after_transfers_taxes"]].rename(
        columns={"adj_inc_after_transfers_taxes": CBO_PROXY_VALUE_COL}
    )
    out["source"] = CBO_RESEARCHERS_SOURCE
    out["notes"] = CBO_PROXY_NOTES
    return out.sort_values("year").reset_index(drop=True)
