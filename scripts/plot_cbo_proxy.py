"""Plot the starter CBO proxy series.

Run from the repo root:

    python scripts/plot_cbo_proxy.py
"""

from pathlib import Path
import sys

import matplotlib.pyplot as plt

# Allow the script to run before the package is installed.
REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = REPO_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from economics.metrics import add_growth_columns, load_cbo_proxy, summarize_series


DATA_PATH = (
    REPO_ROOT
    / "data"
    / "processed"
    / "cbo_proxy_median_adjusted_income_after_tax_transfer.csv"
)
OUTPUT_PATH = REPO_ROOT / "outputs" / "charts" / "cbo_proxy_median_adjusted_income.png"

VALUE_COL = "median_adjusted_income_after_transfers_taxes_2022_dollars"


def main() -> None:
    df = load_cbo_proxy(DATA_PATH)
    df = add_growth_columns(df, VALUE_COL)
    summary = summarize_series(df, VALUE_COL)

    print("CBO proxy summary")
    print("-----------------")
    for key, value in summary.items():
        if key.endswith("_pct"):
            print(f"{key}: {value:.2f}%")
        elif key.endswith("_value"):
            print(f"{key}: ${value:,.0f}")
        else:
            print(f"{key}: {value}")

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(df["year"], df[VALUE_COL], marker="o", linewidth=2)

    ax.set_title("Median adjusted income after transfers and federal taxes")
    ax.set_xlabel("Year")
    ax.set_ylabel("2022 dollars")
    ax.grid(True, axis="y", alpha=0.3)

    # Keep labels readable and avoid overfitting the chart style.
    ax.yaxis.set_major_formatter(lambda x, pos: f"${x:,.0f}")

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(OUTPUT_PATH, dpi=200)
    print(f"Saved chart to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
