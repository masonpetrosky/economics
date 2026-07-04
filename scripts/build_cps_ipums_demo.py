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
DEFAULT_PREFLIGHT_OUT = (
    REPO_ROOT / "data" / "processed" / "cps_ipums_preflight_summary.csv"
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
        "--preflight-out",
        type=Path,
        default=None,
        help=(
            "Optional path to write per-year CPS/IPUMS QA summary. "
            f"Suggested path: {DEFAULT_PREFLIGHT_OUT}"
        ),
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
    capital_gains_group = parser.add_mutually_exclusive_group()
    capital_gains_group.add_argument(
        "--include-capital-gains",
        action="store_true",
        help=(
            "Include CAPGAIN. For IPUMS-format input, use only when selected years "
            "end by ASEC 2008."
        ),
    )
    capital_gains_group.add_argument(
        "--exclude-capital-gains",
        action="store_true",
        help=(
            "Exclude realized capital gains from resources. This is the default for "
            "IPUMS-format input because CAPGAIN is unavailable after ASEC 2008."
        ),
    )
    health_group = parser.add_mutually_exclusive_group()
    health_group.add_argument(
        "--include-health-insurance",
        action="store_true",
        help=(
            "Include health_insurance_value. For IPUMS-format input, this uses the "
            "starter bridge's zero-filled value unless a custom mapping is added."
        ),
    )
    health_group.add_argument(
        "--exclude-health-insurance",
        action="store_true",
        help=(
            "Exclude health insurance value from resources. This is the default for "
            "IPUMS-format input because the starter bridge zero-fills it."
        ),
    )
    return parser.parse_args()


def _variant_from_args(args: argparse.Namespace) -> object:
    """Build a CPS variant, with safer defaults for IPUMS-format input."""

    from economics.cps import CpsVariant

    if args.input_format == "ipums":
        include_capital_gains = args.include_capital_gains
        include_health_insurance = args.include_health_insurance
    else:
        include_capital_gains = not args.exclude_capital_gains
        include_health_insurance = not args.exclude_health_insurance

    return CpsVariant(
        include_capital_gains=include_capital_gains,
        include_health_insurance=include_health_insurance,
        population=args.population,
    )


def _metadata_for_args(args: argparse.Namespace, variant: object) -> tuple[str, str]:
    """Return source and notes metadata for processed CPS output."""

    from economics.cps import (
        DEFAULT_CPS_NOTES,
        DEFAULT_CPS_SOURCE,
        IPUMS_CPS_NOTES_WITH_CAPITAL_GAINS,
        IPUMS_CPS_NOTES_WITHOUT_CAPITAL_GAINS,
        IPUMS_CPS_SOURCE,
    )

    if args.input_format != "ipums":
        return DEFAULT_CPS_SOURCE, DEFAULT_CPS_NOTES

    notes = (
        IPUMS_CPS_NOTES_WITH_CAPITAL_GAINS
        if variant.include_capital_gains
        else IPUMS_CPS_NOTES_WITHOUT_CAPITAL_GAINS
    )
    return IPUMS_CPS_SOURCE, notes


def main() -> int:
    """Run the CPS/IPUMS build."""

    _add_src_to_path()
    from economics.cps import (
        estimate_cps_annual_medians,
        normalize_ipums_cps_asec_extract,
        summarize_cps_preflight,
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

    variant = _variant_from_args(args)
    if args.preflight_out is not None:
        preflight = summarize_cps_preflight(raw, variant)
        args.preflight_out.parent.mkdir(parents=True, exist_ok=True)
        preflight.to_csv(args.preflight_out, index=False)
        print(f"Wrote {len(preflight)} CPS/IPUMS preflight rows to {args.preflight_out}")

    source, notes = _metadata_for_args(args, variant)
    output = estimate_cps_annual_medians(raw, variant, source=source, notes=notes)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    output.to_csv(args.out, index=False)
    print(f"Wrote {len(output)} CPS/IPUMS median rows to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
