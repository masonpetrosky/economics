"""Build the processed CBO proxy CSV from CBO's official researchers ZIP."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = REPO_ROOT / "src"
DEFAULT_RAW_ZIP = REPO_ROOT / "data" / "raw" / "61911-additional-data-for-researchers.zip"
DEFAULT_OUT = (
    REPO_ROOT
    / "data"
    / "processed"
    / "cbo_proxy_median_adjusted_income_after_tax_transfer.csv"
)


def _add_src_to_path() -> None:
    """Allow direct script execution without requiring package installation."""

    if str(SRC_PATH) not in sys.path:
        sys.path.insert(0, str(SRC_PATH))


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""

    parser = argparse.ArgumentParser(
        description="Build the processed CBO proxy CSV from the CBO researchers ZIP."
    )
    parser.add_argument(
        "--raw-zip",
        type=Path,
        default=DEFAULT_RAW_ZIP,
        help=f"Path to the manually downloaded CBO researchers ZIP. Default: {DEFAULT_RAW_ZIP}",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=DEFAULT_OUT,
        help=f"Processed CSV output path. Default: {DEFAULT_OUT}",
    )
    return parser.parse_args()


def main() -> None:
    """Run the CBO proxy build."""

    _add_src_to_path()
    from economics.cbo import build_cbo_proxy_from_researchers_zip

    args = parse_args()
    df = build_cbo_proxy_from_researchers_zip(args.raw_zip)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.out, index=False)
    print(f"Wrote {len(df)} rows to {args.out}")


if __name__ == "__main__":
    main()
