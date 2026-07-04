"""Convert nominal CPS/IPUMS median resources to real dollars.

Run from the repo root:

    python scripts/build_cps_ipums_real.py
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = REPO_ROOT / "src"
DEFAULT_NOMINAL_CSV = (
    REPO_ROOT
    / "data"
    / "processed"
    / "cps_ipums_median_adult_equivalent_resources.csv"
)
DEFAULT_PRICE_INDEX_CSV = REPO_ROOT / "data" / "raw" / "annual_price_index.csv"
DEFAULT_OUT = (
    REPO_ROOT
    / "data"
    / "processed"
    / "cps_ipums_median_adult_equivalent_resources_real.csv"
)


def _display_source_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return path.name


def _add_src_to_path() -> None:
    """Allow direct script execution without requiring package installation."""

    if str(SRC_PATH) not in sys.path:
        sys.path.insert(0, str(SRC_PATH))


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""

    _add_src_to_path()
    from economics.prices import DEFAULT_REAL_BASE_YEAR

    parser = argparse.ArgumentParser(
        description="Convert nominal CPS/IPUMS median resources to real dollars."
    )
    parser.add_argument(
        "--nominal-csv",
        type=Path,
        default=DEFAULT_NOMINAL_CSV,
        help=f"Nominal CPS/IPUMS processed CSV. Default: {DEFAULT_NOMINAL_CSV}",
    )
    parser.add_argument(
        "--price-index-csv",
        type=Path,
        default=DEFAULT_PRICE_INDEX_CSV,
        help=f"Annual price-index CSV. Default: {DEFAULT_PRICE_INDEX_CSV}",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=DEFAULT_OUT,
        help=f"Real CPS/IPUMS output CSV. Default: {DEFAULT_OUT}",
    )
    parser.add_argument(
        "--base-year",
        type=int,
        default=DEFAULT_REAL_BASE_YEAR,
        help=f"Real-dollar base year. Default: {DEFAULT_REAL_BASE_YEAR}",
    )
    return parser.parse_args()


def main() -> int:
    """Run the CPS/IPUMS real-dollar build."""

    _add_src_to_path()
    from economics.prices import convert_nominal_series_to_real

    args = parse_args()
    if not args.nominal_csv.exists():
        print(f"Expected nominal CPS/IPUMS file not found: {args.nominal_csv}", file=sys.stderr)
        return 1
    if not args.price_index_csv.exists():
        print(
            f"Expected annual price-index file not found: {args.price_index_csv}",
            file=sys.stderr,
        )
        return 1

    nominal = pd.read_csv(args.nominal_csv)
    price_index = pd.read_csv(args.price_index_csv)
    output = convert_nominal_series_to_real(
        nominal,
        price_index,
        base_year=args.base_year,
    )
    if "notes" in output.columns:
        price_index_source = _display_source_path(args.price_index_csv)
        output["notes"] = (
            output["notes"].astype(str)
            + f" Converted to {args.base_year} real dollars using {price_index_source}."
        )

    args.out.parent.mkdir(parents=True, exist_ok=True)
    output.to_csv(args.out, index=False)
    print(f"Wrote {len(output)} real CPS/IPUMS rows to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
