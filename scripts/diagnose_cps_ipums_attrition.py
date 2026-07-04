"""Profile CPS/IPUMS estimator row attrition by segment."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = REPO_ROOT / "src"
DEFAULT_INPUT_CSV = REPO_ROOT / "data" / "interim" / "ipums_cps_asec_extract.csv"
DEFAULT_OUT = REPO_ROOT / "outputs" / "tables" / "cps_ipums_attrition_diagnostics.csv"


def _add_src_to_path() -> None:
    """Allow direct script execution without requiring package installation."""

    if str(SRC_PATH) not in sys.path:
        sys.path.insert(0, str(SRC_PATH))


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""

    parser = argparse.ArgumentParser(
        description="Write CPS/IPUMS estimator row-attrition diagnostics by segment."
    )
    parser.add_argument(
        "--input-csv",
        type=Path,
        default=DEFAULT_INPUT_CSV,
        help=f"Normalized CPS/IPUMS CSV path. Default: {DEFAULT_INPUT_CSV}",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=DEFAULT_OUT,
        help=f"Diagnostic CSV output path. Default: {DEFAULT_OUT}",
    )
    parser.add_argument(
        "--population",
        choices=["all", "adults"],
        default="all",
        help="Population filter for the diagnostic. Default: all",
    )
    parser.add_argument(
        "--include-capital-gains",
        action="store_true",
        help=(
            "Include realized capital gains in required estimator inputs. Default is "
            "excluded to match the full-span starter IPUMS build."
        ),
    )
    parser.add_argument(
        "--include-health-insurance",
        action="store_true",
        help=(
            "Include health insurance value in required estimator inputs. Default is "
            "excluded to match the starter IPUMS build."
        ),
    )
    return parser.parse_args()


def main() -> int:
    """Run the attrition diagnostic."""

    _add_src_to_path()
    from economics.cps import CpsVariant, diagnose_cps_estimation_attrition

    args = parse_args()
    if not args.input_csv.exists():
        print(
            f"Expected normalized CPS/IPUMS input file not found: {args.input_csv}",
            file=sys.stderr,
        )
        return 1

    raw = pd.read_csv(args.input_csv)
    variant = CpsVariant(
        include_capital_gains=args.include_capital_gains,
        include_health_insurance=args.include_health_insurance,
        population=args.population,
    )
    diagnostics = diagnose_cps_estimation_attrition(raw, variant)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    diagnostics.to_csv(args.out, index=False)
    print(f"Wrote {len(diagnostics)} CPS/IPUMS attrition diagnostic rows to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
