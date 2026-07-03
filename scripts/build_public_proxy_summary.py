"""Build a summary table for the public proxy and comparison series.

Run from the repo root:

    python scripts/build_public_proxy_summary.py
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = REPO_ROOT / "src"
DEFAULT_OUT = REPO_ROOT / "outputs" / "tables" / "public_proxy_summary.csv"


def _add_src_to_path() -> None:
    """Allow direct script execution without requiring package installation."""

    if str(SRC_PATH) not in sys.path:
        sys.path.insert(0, str(SRC_PATH))


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""

    parser = argparse.ArgumentParser(
        description="Build the public proxy comparison summary table."
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=DEFAULT_OUT,
        help=f"Summary CSV output path. Default: {DEFAULT_OUT}",
    )
    return parser.parse_args()


def main() -> None:
    """Run the public proxy summary build."""

    _add_src_to_path()

    from economics.loaders import CBO_PROXY_VALUE_COL, load_cbo_proxy
    from economics.tables import build_comparison_summary

    args = parse_args()
    series_frames = _load_public_proxy_series(CBO_PROXY_VALUE_COL, load_cbo_proxy)
    table = build_comparison_summary(series_frames)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    table.to_csv(args.out, index=False)
    print(f"Wrote {len(table)} summary rows to {args.out}")


def _load_public_proxy_series(
    cbo_value_col: str,
    load_cbo_proxy_fn,
) -> dict[str, pd.DataFrame]:
    """Load processed public proxy files as year/value DataFrames."""

    from economics.paths import processed_data_path

    cbo = load_cbo_proxy_fn(
        processed_data_path("cbo_proxy_median_adjusted_income_after_tax_transfer.csv")
    )
    series_frames = {
        "CBO adjusted income after transfers and taxes": cbo[["year", cbo_value_col]].rename(
            columns={cbo_value_col: "value"}
        )
    }

    for filename in [
        "fred_real_median_personal_income.csv",
        "fred_real_median_household_income.csv",
        "fred_real_disposable_personal_income_per_capita.csv",
    ]:
        df = pd.read_csv(processed_data_path(filename))
        series_name = str(df["series"].iloc[0])
        series_frames[series_name] = df[["year", "value"]]

    return series_frames


if __name__ == "__main__":
    main()
