from __future__ import annotations

import subprocess
import sys
import zipfile
from pathlib import Path

import pandas as pd
import pytest

from economics.cbo import CBO_RESEARCHERS_ZIP_MEMBER, build_cbo_proxy_from_researchers_zip
from economics.loaders import CBO_PROXY_VALUE_COL
from economics.paths import repo_root


def _write_researchers_zip(
    path: Path,
    csv_text: str,
    member: str = CBO_RESEARCHERS_ZIP_MEMBER,
) -> None:
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr(member, csv_text)


def test_build_cbo_proxy_from_researchers_zip_extracts_adjusted_after_tax_median(
    tmp_path: Path,
) -> None:
    raw_zip = tmp_path / "cbo.zip"
    _write_researchers_zip(
        raw_zip,
        "\n".join(
            [
                "year,market_inc,adj_market_inc,inc_after_transfers_taxes,adj_inc_after_transfers_taxes",
                "1980,67500,36900,59100,32100",
                "1979,70700,38300,60800,33100",
            ]
        ),
    )

    df = build_cbo_proxy_from_researchers_zip(raw_zip)

    assert df.to_dict("records") == [
        {
            "year": 1979,
            CBO_PROXY_VALUE_COL: 33100,
            "source": "CBO Distribution of Household Income, 2022 Additional Data for Researchers",
            "notes": (
                "Median adjusted household income after transfers and federal taxes; "
                "2022 dollars; households ranked by income after transfers and taxes."
            ),
        },
        {
            "year": 1980,
            CBO_PROXY_VALUE_COL: 32100,
            "source": "CBO Distribution of Household Income, 2022 Additional Data for Researchers",
            "notes": (
                "Median adjusted household income after transfers and federal taxes; "
                "2022 dollars; households ranked by income after transfers and taxes."
            ),
        },
    ]


def test_build_cbo_proxy_from_researchers_zip_reports_missing_member(tmp_path: Path) -> None:
    raw_zip = tmp_path / "cbo.zip"
    _write_researchers_zip(raw_zip, "year,adj_inc_after_transfers_taxes\n1979,33100", "other.csv")

    with pytest.raises(ValueError, match="does not contain expected CBO member"):
        build_cbo_proxy_from_researchers_zip(raw_zip)


def test_build_cbo_proxy_from_researchers_zip_reports_missing_columns(tmp_path: Path) -> None:
    raw_zip = tmp_path / "cbo.zip"
    _write_researchers_zip(raw_zip, "year,wrong\n1979,33100")

    with pytest.raises(
        ValueError,
        match="missing required columns: \\['adj_inc_after_transfers_taxes'\\]",
    ):
        build_cbo_proxy_from_researchers_zip(raw_zip)


def test_build_cbo_proxy_script_writes_processed_csv(tmp_path: Path) -> None:
    raw_zip = tmp_path / "cbo.zip"
    out = tmp_path / "processed.csv"
    _write_researchers_zip(
        raw_zip,
        "\n".join(
            [
                "year,market_inc,adj_market_inc,inc_after_transfers_taxes,adj_inc_after_transfers_taxes",
                "1979,70700,38300,60800,33100",
            ]
        ),
    )

    result = subprocess.run(
        [
            sys.executable,
            str(repo_root() / "scripts" / "build_cbo_proxy.py"),
            "--raw-zip",
            str(raw_zip),
            "--out",
            str(out),
        ],
        cwd=repo_root(),
        check=True,
        capture_output=True,
        text=True,
    )

    df = pd.read_csv(out)
    assert df[["year", CBO_PROXY_VALUE_COL]].to_dict("records") == [
        {"year": 1979, CBO_PROXY_VALUE_COL: 33100}
    ]
    assert "Wrote 1 rows" in result.stdout
