"""Plot the starter CBO proxy series.

Run from the repo root:

    python scripts/plot_cbo_proxy.py
"""

import sys
from pathlib import Path

import matplotlib.pyplot as plt

# Allow the script to run before the package is installed.
REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = REPO_ROOT / "src"


def _add_src_to_path() -> None:
    if str(SRC_PATH) not in sys.path:
        sys.path.insert(0, str(SRC_PATH))


def main() -> None:
    _add_src_to_path()

    from economics.charts import plot_time_series
    from economics.loaders import CBO_PROXY_VALUE_COL, load_cbo_proxy
    from economics.paths import output_path, processed_data_path
    from economics.series import add_growth_columns
    from economics.tables import build_summary_table

    data_path = processed_data_path("cbo_proxy_median_adjusted_income_after_tax_transfer.csv")
    output_chart_path = output_path("charts", "cbo_proxy_median_adjusted_income.png")

    df = load_cbo_proxy(data_path)
    df = add_growth_columns(df, CBO_PROXY_VALUE_COL)
    summary = build_summary_table(
        df,
        CBO_PROXY_VALUE_COL,
        label="CBO median adjusted income after transfers and federal taxes",
    )

    print("CBO proxy summary")
    print("-----------------")
    for row in summary.to_dict("records"):
        metric = row["metric"]
        value = row["value"]
        if metric.endswith("_pct"):
            print(f"{metric}: {value:.2f}%")
        elif metric.endswith("_value"):
            print(f"{metric}: ${value:,.0f}")
        else:
            print(f"{metric}: {value:.0f}")

    fig, _ax = plot_time_series(
        df,
        CBO_PROXY_VALUE_COL,
        title="Median adjusted income after transfers and federal taxes",
        ylabel="2022 dollars",
        output_path=output_chart_path,
    )
    plt.close(fig)
    print(f"Saved chart to {output_chart_path}")


if __name__ == "__main__":
    main()
