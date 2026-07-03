"""Build processed FRED comparison CSVs from manually downloaded raw exports."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = REPO_ROOT / "src"
DEFAULT_RAW_DIR = REPO_ROOT / "data" / "raw"
DEFAULT_PROCESSED_DIR = REPO_ROOT / "data" / "processed"


def _add_src_to_path() -> None:
    """Allow direct script execution without requiring package installation."""

    if str(SRC_PATH) not in sys.path:
        sys.path.insert(0, str(SRC_PATH))


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""

    parser = argparse.ArgumentParser(
        description="Build processed FRED comparison CSVs from raw exports."
    )
    parser.add_argument(
        "--raw-dir",
        type=Path,
        default=DEFAULT_RAW_DIR,
        help=f"Directory containing manually downloaded FRED CSVs. Default: {DEFAULT_RAW_DIR}",
    )
    parser.add_argument(
        "--processed-dir",
        type=Path,
        default=DEFAULT_PROCESSED_DIR,
        help=f"Processed CSV output directory. Default: {DEFAULT_PROCESSED_DIR}",
    )
    return parser.parse_args()


def main() -> None:
    """Run the FRED comparison build."""

    _add_src_to_path()
    from economics.fred import build_all_fred_series

    args = parse_args()
    outputs = build_all_fred_series(args.raw_dir, args.processed_dir)
    print(f"Wrote {len(outputs)} FRED comparison files")
    for key, output_path in outputs.items():
        print(f"{key}: {output_path}")


if __name__ == "__main__":
    main()
