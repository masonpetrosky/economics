from __future__ import annotations

import pandas as pd
import pytest

from economics.prices import (
    DEFAULT_REAL_BASE_YEAR,
    convert_nominal_series_to_real,
    validate_annual_price_index,
)


def test_validate_annual_price_index_returns_sorted_numeric_rows() -> None:
    df = pd.DataFrame({"year": ["2024", "2023"], "price_index": ["125.0", "100.0"]})

    out = validate_annual_price_index(df, "test price index")

    assert out.to_dict("records") == [
        {"year": 2023, "price_index": 100.0},
        {"year": 2024, "price_index": 125.0},
    ]


def test_validate_annual_price_index_reports_missing_columns() -> None:
    df = pd.DataFrame({"year": [2024]})

    with pytest.raises(
        ValueError,
        match="test price index missing required columns: \\['price_index'\\]",
    ):
        validate_annual_price_index(df, "test price index")


def test_validate_annual_price_index_rejects_nonnumeric_values() -> None:
    df = pd.DataFrame({"year": [2024, "bad"], "price_index": [125.0, 100.0]})

    with pytest.raises(ValueError, match="test price index has nonnumeric year values"):
        validate_annual_price_index(df, "test price index")


def test_validate_annual_price_index_rejects_duplicate_years() -> None:
    df = pd.DataFrame({"year": [2024, 2024], "price_index": [125.0, 126.0]})

    with pytest.raises(ValueError, match="test price index has duplicate years: 2024"):
        validate_annual_price_index(df, "test price index")


def test_validate_annual_price_index_rejects_nonpositive_values() -> None:
    df = pd.DataFrame({"year": [2023, 2024], "price_index": [0.0, 125.0]})

    with pytest.raises(
        ValueError,
        match="test price index has nonpositive price_index values for years: 2023",
    ):
        validate_annual_price_index(df, "test price index")


def test_convert_nominal_series_to_real_uses_requested_base_year() -> None:
    nominal = pd.DataFrame(
        {
            "year": [2023, 2024],
            "value": [100.0, 200.0],
            "series": ["Nominal CPS", "Nominal CPS"],
            "source": ["fixture", "fixture"],
        }
    )
    prices = pd.DataFrame({"year": [2023, 2024], "price_index": [100.0, 125.0]})

    out = convert_nominal_series_to_real(nominal, prices, base_year=2024)

    assert out.to_dict("records") == [
        {
            "year": 2023,
            "value": 125.0,
            "nominal_value": 100.0,
            "price_index": 100.0,
            "real_base_year": 2024,
            "series": "Nominal CPS",
            "source": "fixture",
        },
        {
            "year": 2024,
            "value": 200.0,
            "nominal_value": 200.0,
            "price_index": 125.0,
            "real_base_year": 2024,
            "series": "Nominal CPS",
            "source": "fixture",
        },
    ]


def test_convert_nominal_series_to_real_defaults_to_2024_base_year() -> None:
    nominal = pd.DataFrame({"year": [2024], "value": [100.0]})
    prices = pd.DataFrame({"year": [2024], "price_index": [125.0]})

    out = convert_nominal_series_to_real(nominal, prices)

    assert DEFAULT_REAL_BASE_YEAR == 2024
    assert out["real_base_year"].tolist() == [2024]


def test_convert_nominal_series_to_real_rejects_missing_nominal_columns() -> None:
    nominal = pd.DataFrame({"year": [2024]})
    prices = pd.DataFrame({"year": [2024], "price_index": [125.0]})

    with pytest.raises(ValueError, match="nominal series missing required columns: \\['value'\\]"):
        convert_nominal_series_to_real(nominal, prices)


def test_convert_nominal_series_to_real_rejects_missing_price_years() -> None:
    nominal = pd.DataFrame({"year": [2023, 2024], "value": [100.0, 200.0]})
    prices = pd.DataFrame({"year": [2024], "price_index": [125.0]})

    with pytest.raises(
        ValueError,
        match="price index missing years required by nominal series: 2023",
    ):
        convert_nominal_series_to_real(nominal, prices, base_year=2024)


def test_convert_nominal_series_to_real_rejects_missing_base_year() -> None:
    nominal = pd.DataFrame({"year": [2023], "value": [100.0]})
    prices = pd.DataFrame({"year": [2023], "price_index": [100.0]})

    with pytest.raises(ValueError, match="price index missing requested base year: 2024"):
        convert_nominal_series_to_real(nominal, prices, base_year=2024)
