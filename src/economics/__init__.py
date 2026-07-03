"""Economics data-project package."""

from economics.cbo import build_cbo_proxy_from_researchers_zip
from economics.equivalence import equivalize_resources, square_root_equivalence_scale
from economics.fred import FRED_SERIES, FredSeriesSpec, build_all_fred_series, build_fred_series
from economics.loaders import CBO_PROXY_VALUE_COL, load_cbo_proxy, load_comparison_series
from economics.resources import ResourceComponents
from economics.series import add_growth_columns, real_value, summarize_series, weighted_median
from economics.tables import build_comparison_summary

__all__ = [
    "CBO_PROXY_VALUE_COL",
    "FRED_SERIES",
    "ResourceComponents",
    "FredSeriesSpec",
    "add_growth_columns",
    "build_all_fred_series",
    "build_comparison_summary",
    "build_cbo_proxy_from_researchers_zip",
    "build_fred_series",
    "equivalize_resources",
    "load_cbo_proxy",
    "load_comparison_series",
    "real_value",
    "square_root_equivalence_scale",
    "summarize_series",
    "weighted_median",
]
