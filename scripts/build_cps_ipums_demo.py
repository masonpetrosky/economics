"""Build a CPS/IPUMS median resources CSV from a manual extract.

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
DEFAULT_NORMALIZED_RAW_CSV = REPO_ROOT / "data" / "raw" / "ipums_cps_asec_extract.csv"
DEFAULT_IPUMS_RAW_CSV = REPO_ROOT / "data" / "raw" / "ipums_cps_asec_raw.csv"
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
        description="Build CPS/IPUMS median adult-equivalent resources from manual input."
    )
    parser.add_argument(
        "--input-format",
        choices=["normalized", "ipums"],
        default="normalized",
        help=(
            "Input schema. Use 'normalized' for the project contract or 'ipums' for "
            "the documented rectangularized IPUMS CPS ASEC export. Default: normalized"
        ),
    )
    parser.add_argument(
        "--raw-csv",
        type=Path,
        default=None,
        help=(
            "Manual input CSV. Defaults to "
            f"{DEFAULT_NORMALIZED_RAW_CSV} for normalized input or {DEFAULT_IPUMS_RAW_CSV} "
            "for IPUMS input."
        ),
    )
    parser.add_argument(
        "--normalized-out",
        type=Path,
        default=None,
        help="Optional path to write normalized person rows before estimating medians.",
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
    from economics.cps import (
        CpsVariant,
        estimate_cps_annual_medians,
        normalize_ipums_cps_asec_extract,
    )

    args = parse_args()
    raw_csv = args.raw_csv or (
        DEFAULT_IPUMS_RAW_CSV
        if args.input_format == "ipums"
        else DEFAULT_NORMALIZED_RAW_CSV
    )
    if not raw_csv.exists():
        print(f"Expected CPS/IPUMS input file not found: {raw_csv}", file=sys.stderr)
        return 1

    raw = pd.read_csv(raw_csv)
    if args.input_format == "ipums":
        raw = normalize_ipums_cps_asec_extract(raw)

    if args.normalized_out is not None:
        args.normalized_out.parent.mkdir(parents=True, exist_ok=True)
        raw.to_csv(args.normalized_out, index=False)
        print(f"Wrote {len(raw)} normalized CPS/IPUMS rows to {args.normalized_out}")

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
