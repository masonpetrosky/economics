import math

import pandas as pd
import pytest

from economics.equivalence import equivalize_resources, square_root_equivalence_scale
from economics.resources import ResourceComponents
from economics.series import add_growth_columns, real_value, summarize_series, weighted_median


def test_square_root_equivalence_scale_uses_household_size_root() -> None:
    assert square_root_equivalence_scale(4) == 2


def test_square_root_equivalence_scale_rejects_nonpositive_size() -> None:
    with pytest.raises(ValueError, match="household_size must be positive"):
        square_root_equivalence_scale(0)


def test_equivalize_resources_divides_by_scale() -> None:
    assert equivalize_resources(80_000, 4) == 40_000


def test_resource_components_subtract_taxes_from_broad_resources() -> None:
    components = ResourceComponents(
        money_income=50_000,
        realized_capital_gains=2_000,
        noncash_benefits=5_000,
        health_insurance_value=8_000,
        federal_income_taxes=4_000,
        payroll_taxes=3_000,
        state_local_income_taxes=1_000,
    )

    assert components.comprehensive_disposable_resources() == 57_000


def test_weighted_median_returns_first_value_at_half_weight_cutoff() -> None:
    assert weighted_median([10, 20, 30], [1, 2, 1]) == 20


def test_weighted_median_rejects_no_positive_weights() -> None:
    with pytest.raises(ValueError, match="No positive-weight observations"):
        weighted_median([10, 20], [0, 0])


def test_real_value_scales_nominal_value_to_base_price_index() -> None:
    assert real_value(nominal_value=100, price_index=200, base_price_index=250) == 125


def test_real_value_rejects_nonpositive_price_index() -> None:
    with pytest.raises(ValueError, match="price_index must be positive"):
        real_value(nominal_value=100, price_index=0, base_price_index=250)


def test_add_growth_columns_adds_yoy_cumulative_and_annualized_growth() -> None:
    df = pd.DataFrame({"year": [2000, 2001, 2002], "value": [100, 110, 121]})

    out = add_growth_columns(df, "value")

    assert math.isnan(out.loc[0, "value_yoy_pct"])
    assert out["value_yoy_pct"].iloc[1:].round(2).tolist() == [10.0, 10.0]
    assert out["value_cumulative_pct"].round(2).tolist() == [0.0, 10.0, 21.0]
    assert math.isnan(out.loc[0, "value_annualized_pct"])
    assert round(out.loc[2, "value_annualized_pct"], 2) == 10.0


def test_summarize_series_returns_start_end_and_growth() -> None:
    df = pd.DataFrame({"year": [2000, 2002], "value": [100, 121]})

    summary = summarize_series(df, "value")

    assert summary == {
        "start_year": 2000,
        "end_year": 2002,
        "start_value": 100.0,
        "end_value": 121.0,
        "cumulative_growth_pct": pytest.approx(21.0),
        "annualized_growth_pct": pytest.approx(10.0),
    }
