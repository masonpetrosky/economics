"""Compatibility facade for core metric helpers.

New code should import from the focused modules directly. This module keeps the
starter script and early notebooks stable while the package structure matures.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from economics.equivalence import equivalize_resources, square_root_equivalence_scale
from economics.resources import ResourceComponents
from economics.series import add_growth_columns, real_value, summarize_series, weighted_median

CBO_PROXY_VALUE_COL = "median_adjusted_income_after_transfers_taxes_2022_dollars"


def load_cbo_proxy(path: str | Path) -> pd.DataFrame:
    """Load the starter CBO proxy CSV.

    The dedicated loader module added in the next task will own this behavior.
    This compatibility copy keeps the existing plotting script runnable after
    the core metric split.
    """

    path = Path(path)
    df = pd.read_csv(path)

    required = {"year", CBO_PROXY_VALUE_COL}
    missing = sorted(required.difference(df.columns))
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    return df.sort_values("year").reset_index(drop=True)


__all__ = [
    "CBO_PROXY_VALUE_COL",
    "ResourceComponents",
    "add_growth_columns",
    "equivalize_resources",
    "load_cbo_proxy",
    "real_value",
    "square_root_equivalence_scale",
    "summarize_series",
    "weighted_median",
]
