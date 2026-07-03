"""Plot indexed public proxy and comparison income/resource series.

Run from the repo root:

    python scripts/plot_public_proxies.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = REPO_ROOT / "src"


def _add_src_to_path() -> None:
    if str(SRC_PATH) not in sys.path:
        sys.path.insert(0, str(SRC_PATH))


def main() -> None:
    """Build an indexed comparison chart from processed public proxy files."""

    _add_src_to_path()

    from economics.charts import plot_multiple_series
    from economics.loaders import CBO_PROXY_VALUE_COL, load_cbo_proxy
    from economics.paths import output_path, processed_data_path

    cbo = load_cbo_proxy(
        processed_data_path("cbo_proxy_median_adjusted_income_after_tax_transfer.csv")
    )
    tidy = [
        cbo[["year", CBO_PROXY_VALUE_COL]]
        .rename(columns={CBO_PROXY_VALUE_COL: "value"})
        .assign(series="CBO adjusted income after transfers and taxes")
    ]

    for filename in [
        "fred_real_median_personal_income.csv",
        "fred_real_median_household_income.csv",
        "fred_real_disposable_personal_income_per_capita.csv",
    ]:
        df = pd.read_csv(processed_data_path(filename))
        tidy.append(df[["year", "value", "series"]])

    combined = pd.concat(tidy, ignore_index=True).sort_values(["series", "year"])
    combined["index_value"] = combined.groupby("series")["value"].transform(
        lambda values: values / values.iloc[0] * 100
    )

    output_chart_path = output_path("charts", "public_proxy_comparison.png")
    fig, _ax = plot_multiple_series(
        combined,
        value_col="index_value",
        title="Public income/resource proxy comparison",
        ylabel="Index, first observation = 100",
        output_path=output_chart_path,
    )
    plt.close(fig)
    print(f"Saved chart to {output_chart_path}")


if __name__ == "__main__":
    main()
