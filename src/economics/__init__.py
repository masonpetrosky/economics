"""Economics data-project package."""

from economics.cbo import build_cbo_proxy_from_researchers_zip
from economics.cps import (
    CpsVariant,
    IpumsCpsAsecMapping,
    build_cps_person_resources,
    diagnose_cps_estimation_attrition,
    estimate_cps_annual_medians,
    normalize_ipums_cps_asec_extract,
    summarize_cps_preflight,
)
from economics.equivalence import equivalize_resources, square_root_equivalence_scale
from economics.fred import FRED_SERIES, FredSeriesSpec, build_all_fred_series, build_fred_series
from economics.loaders import CBO_PROXY_VALUE_COL, load_cbo_proxy, load_comparison_series
from economics.prices import (
    DEFAULT_REAL_BASE_YEAR,
    PRICE_INDEX_REQUIRED_COLUMNS,
    convert_nominal_series_to_real,
    validate_annual_price_index,
)
from economics.resources import ResourceComponents
from economics.series import add_growth_columns, real_value, summarize_series, weighted_median
from economics.tables import build_comparison_summary

__all__ = [
    "CBO_PROXY_VALUE_COL",
    "CpsVariant",
    "DEFAULT_REAL_BASE_YEAR",
    "FRED_SERIES",
    "ResourceComponents",
    "FredSeriesSpec",
    "IpumsCpsAsecMapping",
    "PRICE_INDEX_REQUIRED_COLUMNS",
    "add_growth_columns",
    "build_all_fred_series",
    "build_comparison_summary",
    "build_cbo_proxy_from_researchers_zip",
    "build_cps_person_resources",
    "build_fred_series",
    "convert_nominal_series_to_real",
    "diagnose_cps_estimation_attrition",
    "equivalize_resources",
    "estimate_cps_annual_medians",
    "load_cbo_proxy",
    "load_comparison_series",
    "normalize_ipums_cps_asec_extract",
    "real_value",
    "square_root_equivalence_scale",
    "summarize_cps_preflight",
    "summarize_series",
    "validate_annual_price_index",
    "weighted_median",
]
