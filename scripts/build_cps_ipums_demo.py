"""Build a CPS/IPUMS median resources CSV from a normalized manual extract.

Run from the repo root:

    python scripts/build_cps_ipums_demo.py
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = REPO_ROOT / "src"
DEFAULT_RAW_CSV = REPO_ROOT / "data" / "raw" / "ipums_cps_asec_extract.csv"
DEFAULT_OUT = (
    REPO_ROOT
    / "data"
    / "processed"
    / "cps_ipums_median_adult_equivalent_resources.csv"
)


def _add_src_to_path() -> None:
    """Allow direct script execution without requiring package installation."""

    if str(SRC_PATH) not in sys.path:
        sys.path.insert(0, str(SRC_PATH))


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""

    parser = argparse.ArgumentParser(
        description="Build CPS/IPUMS median adult-equivalent resources from normalized input."
    )
    parser.add_argument(
        "--raw-csv",
        type=Path,
        default=DEFAULT_RAW_CSV,
        help=f"Normalized CPS/IPUMS input CSV. Default: {DEFAULT_RAW_CSV}",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=DEFAULT_OUT,
        help=f"Processed CSV output path. Default: {DEFAULT_OUT}",
    )
    parser.add_argument(
        "--population",
        choices=["all", "adults"],
        default="all",
        help="Population filter for the median estimate. Default: all",
    )
    parser.add_argument(
        "--exclude-capital-gains",
        action="store_true",
        help="Exclude realized capital gains from resources.",
    )
    parser.add_argument(
        "--exclude-health-insurance",
        action="store_true",
        help="Exclude health insurance value from resources.",
    )
    return parser.parse_args()


def main() -> int:
    """Run the CPS/IPUMS build."""

    _add_src_to_path()
    from economics.cps import CpsVariant, estimate_cps_annual_medians

    args = parse_args()
    if not args.raw_csv.exists():
        print(f"Expected CPS/IPUMS input file not found: {args.raw_csv}", file=sys.stderr)
        return 1

    raw = pd.read_csv(args.raw_csv)
    variant = CpsVariant(
        include_capital_gains=not args.exclude_capital_gains,
        include_health_insurance=not args.exclude_health_insurance,
        population=args.population,
    )
    output = estimate_cps_annual_medians(raw, variant)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    output.to_csv(args.out, index=False)
    print(f"Wrote {len(output)} CPS/IPUMS median rows to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
