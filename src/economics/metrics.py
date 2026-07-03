"""Compatibility facade for core metric helpers.

New code should import from the focused modules directly. This module keeps the
starter script and early notebooks stable while the package structure matures.
"""

from __future__ import annotations

from economics.equivalence import equivalize_resources, square_root_equivalence_scale
from economics.loaders import CBO_PROXY_VALUE_COL, load_cbo_proxy, load_comparison_series
from economics.resources import ResourceComponents
from economics.series import add_growth_columns, real_value, summarize_series, weighted_median

__all__ = [
    "CBO_PROXY_VALUE_COL",
    "ResourceComponents",
    "add_growth_columns",
    "equivalize_resources",
    "load_cbo_proxy",
    "load_comparison_series",
    "real_value",
    "square_root_equivalence_scale",
    "summarize_series",
    "weighted_median",
]
