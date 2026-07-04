"""Build CPS/IPUMS public-proxy QA table and indexed chart.

Run from the repo root:

    python scripts/build_cps_public_proxy_qa.py
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib.pyplot as plt

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = REPO_ROOT / "src"
DEFAULT_PROCESSED_DIR = REPO_ROOT / "data" / "processed"
DEFAULT_TABLE_OUT = REPO_ROOT / "outputs" / "tables" / "cps_public_proxy_qa_summary.csv"
DEFAULT_CHART_OUT = REPO_ROOT / "outputs" / "charts" / "cps_public_proxy_indexed_comparison.png"


def _add_src_to_path() -> None:
    """Allow direct script execution without requiring package installation."""

    if str(SRC_PATH) not in sys.path:
        sys.path.insert(0, str(SRC_PATH))


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""

    parser = argparse.ArgumentParser(
        description="Build CPS/IPUMS public-proxy QA table and indexed chart."
    )
    parser.add_argument(
        "--processed-dir",
        type=Path,
        default=DEFAULT_PROCESSED_DIR,
        help=f"Directory containing processed project CSVs. Default: {DEFAULT_PROCESSED_DIR}",
    )
    parser.add_argument(
        "--table-out",
        type=Path,
        default=DEFAULT_TABLE_OUT,
        help=f"QA table output path. Default: {DEFAULT_TABLE_OUT}",
    )
    parser.add_argument(
        "--chart-out",
        type=Path,
        default=DEFAULT_CHART_OUT,
        help=f"QA chart output path. Default: {DEFAULT_CHART_OUT}",
    )
    return parser.parse_args()


def main() -> int:
    """Run the CPS/IPUMS public-proxy QA build."""

    _add_src_to_path()
    from economics.charts import plot_multiple_series
    from economics.proxy_qa import build_indexed_common_overlap, load_cps_public_proxy_series

    args = parse_args()
    series_frames = load_cps_public_proxy_series(args.processed_dir)
    table = build_indexed_common_overlap(series_frames)

    args.table_out.parent.mkdir(parents=True, exist_ok=True)
    table.to_csv(args.table_out, index=False)
    print(f"Wrote {len(table)} QA rows to {args.table_out}")

    fig, _ax = plot_multiple_series(
        table,
        value_col="index_value",
        title="CPS/IPUMS and public proxy indexed QA comparison",
        ylabel="Index, common start year = 100",
        output_path=args.chart_out,
    )
    plt.close(fig)
    print(f"Saved QA chart to {args.chart_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
