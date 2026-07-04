# CPS/IPUMS Real-Dollar QA Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convert the CPS/IPUMS annual median resource series from nominal dollars into documented real dollars and add an indexed QA comparison against the public proxy series.

**Architecture:** Add a focused `economics.prices` module for annual price-index validation and real-dollar conversion. Keep CPS/IPUMS nominal estimation in `economics.cps`, add one script for real-dollar CPS output, and add one QA module/script for indexed comparison tables and charts from processed outputs.

**Tech Stack:** Python 3.12, pandas, matplotlib, pathlib, argparse, pytest, ruff.

## Global Constraints

- External downloads remain manual.
- The annual price-index file path is `data/raw/annual_price_index.csv`.
- The price-index CSV requires `year` and `price_index`.
- Optional price-index metadata columns may be present but are not required.
- Default real-dollar base year is `2024`.
- Preserve `data/processed/cps_ipums_median_adult_equivalent_resources.csv` as the nominal CPS/IPUMS output.
- Write real CPS/IPUMS output to `data/processed/cps_ipums_median_adult_equivalent_resources_real.csv`.
- Write QA table to `outputs/tables/cps_public_proxy_qa_summary.csv`.
- Write QA chart to `outputs/charts/cps_public_proxy_indexed_comparison.png`.
- Do not download price-index data automatically.
- Do not claim the CPS/IPUMS real output is publication-ready.
- Use `FF_TMPDIR=/tmp TMPDIR=/tmp TMP=/tmp TEMP=/tmp` with pytest in this WSL environment.

---

## File Structure

- Create `src/economics/prices.py`: annual price-index validation and real-dollar conversion.
- Modify `src/economics/loaders.py`: add the annual price-index raw source contract.
- Modify `src/economics/__init__.py`: export price-index helpers.
- Create `tests/test_prices.py`: unit tests for price validation and conversion.
- Create `scripts/build_cps_ipums_real.py`: CLI that reads nominal CPS output and annual price index, then writes real CPS output.
- Create `tests/test_cps_ipums_real.py`: CLI tests for real CPS output writing and missing price-index failure.
- Create `src/economics/proxy_qa.py`: load processed CPS/CBO/FRED frames and build indexed common-overlap QA rows.
- Create `scripts/build_cps_public_proxy_qa.py`: CLI that writes the QA table and chart.
- Create `tests/test_cps_public_proxy_qa.py`: unit and CLI tests for indexed QA output.
- Modify `README.md`: document annual price-index input, real CPS build, and QA workflow.
- Modify `docs/data_sources.md`: document the manual price-index source contract.
- Modify `docs/methodology.md`: clarify nominal versus real CPS/IPUMS output and remaining concept caveats.
- Modify `tests/test_notebook.py`: add lightweight documentation guardrails.

---

### Task 1: Annual Price-Index Core

**Files:**
- Create: `tests/test_prices.py`
- Create: `src/economics/prices.py`
- Modify: `src/economics/loaders.py`
- Modify: `src/economics/__init__.py`

**Interfaces:**
- Consumes:
  - `economics.loaders.validate_required_columns(df, required_columns, source_label) -> None`
  - `economics.series.real_value(nominal_value, price_index, base_price_index) -> float`
- Produces:
  - `PRICE_INDEX_REQUIRED_COLUMNS: tuple[str, str]`
  - `DEFAULT_REAL_BASE_YEAR: int`
  - `validate_annual_price_index(df: pd.DataFrame, source_label: str = "annual price index") -> pd.DataFrame`
  - `convert_nominal_series_to_real(nominal_df: pd.DataFrame, price_index_df: pd.DataFrame, *, base_year: int = DEFAULT_REAL_BASE_YEAR, value_col: str = "value", year_col: str = "year") -> pd.DataFrame`

- [ ] **Step 1: Write failing price-index tests**

Create `tests/test_prices.py` with:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
FF_TMPDIR=/tmp TMPDIR=/tmp TMP=/tmp TEMP=/tmp ./.venv/bin/python -m pytest tests/test_prices.py -q
```

Expected: FAIL during collection with `ModuleNotFoundError: No module named 'economics.prices'`.

- [ ] **Step 3: Add the price-index implementation**

Create `src/economics/prices.py` with:

```python
"""Annual price-index helpers for real-dollar conversion."""

from __future__ import annotations

import pandas as pd

from economics.loaders import validate_required_columns
from economics.series import real_value

PRICE_INDEX_REQUIRED_COLUMNS = ("year", "price_index")
DEFAULT_REAL_BASE_YEAR = 2024


def validate_annual_price_index(
    df: pd.DataFrame,
    source_label: str = "annual price index",
) -> pd.DataFrame:
    """Validate and normalize an annual price-index table."""

    validate_required_columns(df, PRICE_INDEX_REQUIRED_COLUMNS, source_label)

    out = df[list(PRICE_INDEX_REQUIRED_COLUMNS)].copy()
    out["year"] = pd.to_numeric(out["year"], errors="coerce")
    out["price_index"] = pd.to_numeric(out["price_index"], errors="coerce")

    if out["year"].isna().any():
        raise ValueError(f"{source_label} has nonnumeric year values")
    if out["price_index"].isna().any():
        raise ValueError(f"{source_label} has nonnumeric price_index values")

    out["year"] = out["year"].astype(int)

    duplicate_years = sorted(out.loc[out.duplicated("year", keep=False), "year"].unique())
    if duplicate_years:
        raise ValueError(
            f"{source_label} has duplicate years: "
            + ", ".join(str(year) for year in duplicate_years)
        )

    nonpositive_years = sorted(out.loc[out["price_index"] <= 0, "year"].unique())
    if nonpositive_years:
        raise ValueError(
            f"{source_label} has nonpositive price_index values for years: "
            + ", ".join(str(year) for year in nonpositive_years)
        )

    return out.sort_values("year").reset_index(drop=True)


def convert_nominal_series_to_real(
    nominal_df: pd.DataFrame,
    price_index_df: pd.DataFrame,
    *,
    base_year: int = DEFAULT_REAL_BASE_YEAR,
    value_col: str = "value",
    year_col: str = "year",
) -> pd.DataFrame:
    """Convert a nominal annual series to real dollars using an annual price index."""

    validate_required_columns(nominal_df, [year_col, value_col], "nominal series")
    work = nominal_df.copy()
    work[year_col] = pd.to_numeric(work[year_col], errors="coerce")
    work[value_col] = pd.to_numeric(work[value_col], errors="coerce")

    if work[year_col].isna().any():
        raise ValueError("nominal series has nonnumeric year values")
    if work[value_col].isna().any():
        raise ValueError("nominal series has nonnumeric value values")

    work[year_col] = work[year_col].astype(int)
    prices = validate_annual_price_index(price_index_df)
    price_years = set(prices["year"])
    nominal_years = set(work[year_col])

    missing_years = sorted(nominal_years.difference(price_years))
    if missing_years:
        raise ValueError(
            "price index missing years required by nominal series: "
            + ", ".join(str(year) for year in missing_years)
        )

    base_rows = prices.loc[prices["year"] == base_year, "price_index"]
    if base_rows.empty:
        raise ValueError(f"price index missing requested base year: {base_year}")

    base_price_index = float(base_rows.iloc[0])
    merged = work.merge(prices, left_on=year_col, right_on="year", how="left")
    merged["nominal_value"] = merged[value_col].astype(float)
    merged["value"] = [
        real_value(
            nominal_value=float(nominal_value),
            price_index=float(price_index),
            base_price_index=base_price_index,
        )
        for nominal_value, price_index in zip(
            merged["nominal_value"],
            merged["price_index"],
            strict=True,
        )
    ]
    merged["real_base_year"] = int(base_year)

    metadata_cols = [
        column
        for column in nominal_df.columns
        if column not in {year_col, value_col}
    ]
    return merged[
        ["year", "value", "nominal_value", "price_index", "real_base_year", *metadata_cols]
    ].sort_values("year").reset_index(drop=True)
```

- [ ] **Step 4: Add the raw source-file registry entry**

Modify `src/economics/loaders.py` inside `RAW_SOURCE_FILE_SPECS` after the CBO entry:

```python
    "annual_price_index": SourceFileSpec(
        file_name="annual_price_index.csv",
        required_columns=("year", "price_index"),
        description=(
            "Manual annual price-index series used to convert nominal CPS/IPUMS "
            "median resources into base-year real dollars."
        ),
    ),
```

- [ ] **Step 5: Export the price helpers**

Modify `src/economics/__init__.py` by adding:

```python
from economics.prices import (
    DEFAULT_REAL_BASE_YEAR,
    PRICE_INDEX_REQUIRED_COLUMNS,
    convert_nominal_series_to_real,
    validate_annual_price_index,
)
```

Add these names to `__all__`:

```python
    "DEFAULT_REAL_BASE_YEAR",
    "PRICE_INDEX_REQUIRED_COLUMNS",
    "convert_nominal_series_to_real",
    "validate_annual_price_index",
```

- [ ] **Step 6: Run focused price tests**

Run:

```bash
FF_TMPDIR=/tmp TMPDIR=/tmp TMP=/tmp TEMP=/tmp ./.venv/bin/python -m pytest tests/test_prices.py -q
```

Expected: PASS with `10 passed`.

- [ ] **Step 7: Commit Task 1**

Run:

```bash
git add src/economics/prices.py src/economics/loaders.py src/economics/__init__.py tests/test_prices.py
git commit -m "feat: add annual price index helpers"
```

---

### Task 2: CPS/IPUMS Real-Dollar Output Script

**Files:**
- Create: `scripts/build_cps_ipums_real.py`
- Create: `tests/test_cps_ipums_real.py`

**Interfaces:**
- Consumes:
  - `economics.prices.DEFAULT_REAL_BASE_YEAR`
  - `economics.prices.convert_nominal_series_to_real(nominal_df, price_index_df, base_year=2024) -> pd.DataFrame`
- Produces:
  - CLI: `python scripts/build_cps_ipums_real.py`
  - CLI args: `--nominal-csv`, `--price-index-csv`, `--out`, `--base-year`
  - Default input: `data/processed/cps_ipums_median_adult_equivalent_resources.csv`
  - Default price index: `data/raw/annual_price_index.csv`
  - Default output: `data/processed/cps_ipums_median_adult_equivalent_resources_real.csv`

- [ ] **Step 1: Write failing CLI tests**

Create `tests/test_cps_ipums_real.py` with:

```python
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pandas as pd

from economics.paths import repo_root


def test_build_cps_ipums_real_script_writes_real_output(tmp_path: Path) -> None:
    nominal_csv = tmp_path / "nominal.csv"
    price_index_csv = tmp_path / "annual_price_index.csv"
    output_csv = tmp_path / "real.csv"
    nominal_csv.write_text(
        "\n".join(
            [
                "year,value,series,source,variant,include_capital_gains,"
                "include_health_insurance,population,notes",
                "2023,100.0,Median adult-equivalent disposable resources,fixture,"
                "all_without_capital_gains_without_health_insurance,False,False,"
                "all,nominal fixture",
                "2024,200.0,Median adult-equivalent disposable resources,fixture,"
                "all_without_capital_gains_without_health_insurance,False,False,"
                "all,nominal fixture",
            ]
        )
        + "\n"
    )
    price_index_csv.write_text("year,price_index\n2023,100.0\n2024,125.0\n")

    result = subprocess.run(
        [
            sys.executable,
            str(repo_root() / "scripts" / "build_cps_ipums_real.py"),
            "--nominal-csv",
            str(nominal_csv),
            "--price-index-csv",
            str(price_index_csv),
            "--out",
            str(output_csv),
            "--base-year",
            "2024",
        ],
        cwd=repo_root(),
        check=True,
        capture_output=True,
        text=True,
    )

    out = pd.read_csv(output_csv)

    assert f"Wrote 2 real CPS/IPUMS rows to {output_csv}" in result.stdout
    assert list(out.columns) == [
        "year",
        "value",
        "nominal_value",
        "price_index",
        "real_base_year",
        "series",
        "source",
        "variant",
        "include_capital_gains",
        "include_health_insurance",
        "population",
        "notes",
    ]
    assert out[["year", "value", "nominal_value", "price_index", "real_base_year"]].to_dict(
        "records"
    ) == [
        {
            "year": 2023,
            "value": 125.0,
            "nominal_value": 100.0,
            "price_index": 100.0,
            "real_base_year": 2024,
        },
        {
            "year": 2024,
            "value": 200.0,
            "nominal_value": 200.0,
            "price_index": 125.0,
            "real_base_year": 2024,
        },
    ]
    assert "Converted to 2024 real dollars" in out["notes"].iloc[0]


def test_build_cps_ipums_real_script_reports_missing_price_index(tmp_path: Path) -> None:
    nominal_csv = tmp_path / "nominal.csv"
    missing_price_index_csv = tmp_path / "missing_price_index.csv"
    output_csv = tmp_path / "real.csv"
    nominal_csv.write_text("year,value\n2024,200.0\n")

    result = subprocess.run(
        [
            sys.executable,
            str(repo_root() / "scripts" / "build_cps_ipums_real.py"),
            "--nominal-csv",
            str(nominal_csv),
            "--price-index-csv",
            str(missing_price_index_csv),
            "--out",
            str(output_csv),
        ],
        cwd=repo_root(),
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert f"Expected annual price-index file not found: {missing_price_index_csv}" in result.stderr
    assert not output_csv.exists()
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
FF_TMPDIR=/tmp TMPDIR=/tmp TMP=/tmp TEMP=/tmp ./.venv/bin/python -m pytest tests/test_cps_ipums_real.py -q
```

Expected: FAIL because `scripts/build_cps_ipums_real.py` does not exist.

- [ ] **Step 3: Add the real CPS/IPUMS script**

Create `scripts/build_cps_ipums_real.py` with:

```python
"""Convert nominal CPS/IPUMS median resources to real dollars.

Run from the repo root:

    python scripts/build_cps_ipums_real.py
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = REPO_ROOT / "src"
DEFAULT_NOMINAL_CSV = (
    REPO_ROOT
    / "data"
    / "processed"
    / "cps_ipums_median_adult_equivalent_resources.csv"
)
DEFAULT_PRICE_INDEX_CSV = REPO_ROOT / "data" / "raw" / "annual_price_index.csv"
DEFAULT_OUT = (
    REPO_ROOT
    / "data"
    / "processed"
    / "cps_ipums_median_adult_equivalent_resources_real.csv"
)


def _add_src_to_path() -> None:
    """Allow direct script execution without requiring package installation."""

    if str(SRC_PATH) not in sys.path:
        sys.path.insert(0, str(SRC_PATH))


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""

    _add_src_to_path()
    from economics.prices import DEFAULT_REAL_BASE_YEAR

    parser = argparse.ArgumentParser(
        description="Convert nominal CPS/IPUMS median resources to real dollars."
    )
    parser.add_argument(
        "--nominal-csv",
        type=Path,
        default=DEFAULT_NOMINAL_CSV,
        help=f"Nominal CPS/IPUMS processed CSV. Default: {DEFAULT_NOMINAL_CSV}",
    )
    parser.add_argument(
        "--price-index-csv",
        type=Path,
        default=DEFAULT_PRICE_INDEX_CSV,
        help=f"Annual price-index CSV. Default: {DEFAULT_PRICE_INDEX_CSV}",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=DEFAULT_OUT,
        help=f"Real CPS/IPUMS output CSV. Default: {DEFAULT_OUT}",
    )
    parser.add_argument(
        "--base-year",
        type=int,
        default=DEFAULT_REAL_BASE_YEAR,
        help=f"Real-dollar base year. Default: {DEFAULT_REAL_BASE_YEAR}",
    )
    return parser.parse_args()


def main() -> int:
    """Run the CPS/IPUMS real-dollar build."""

    _add_src_to_path()
    from economics.prices import convert_nominal_series_to_real

    args = parse_args()
    if not args.nominal_csv.exists():
        print(f"Expected nominal CPS/IPUMS file not found: {args.nominal_csv}", file=sys.stderr)
        return 1
    if not args.price_index_csv.exists():
        print(
            f"Expected annual price-index file not found: {args.price_index_csv}",
            file=sys.stderr,
        )
        return 1

    nominal = pd.read_csv(args.nominal_csv)
    price_index = pd.read_csv(args.price_index_csv)
    output = convert_nominal_series_to_real(
        nominal,
        price_index,
        base_year=args.base_year,
    )
    if "notes" in output.columns:
        output["notes"] = (
            output["notes"].astype(str)
            + f" Converted to {args.base_year} real dollars using {args.price_index_csv}."
        )

    args.out.parent.mkdir(parents=True, exist_ok=True)
    output.to_csv(args.out, index=False)
    print(f"Wrote {len(output)} real CPS/IPUMS rows to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run focused real-output tests**

Run:

```bash
FF_TMPDIR=/tmp TMPDIR=/tmp TMP=/tmp TEMP=/tmp ./.venv/bin/python -m pytest tests/test_cps_ipums_real.py -q
```

Expected: PASS with `2 passed`.

- [ ] **Step 5: Run price and real-output tests together**

Run:

```bash
FF_TMPDIR=/tmp TMPDIR=/tmp TMP=/tmp TEMP=/tmp ./.venv/bin/python -m pytest tests/test_prices.py tests/test_cps_ipums_real.py -q
```

Expected: PASS with `12 passed`.

- [ ] **Step 6: Commit Task 2**

Run:

```bash
git add scripts/build_cps_ipums_real.py tests/test_cps_ipums_real.py
git commit -m "feat: build real CPS IPUMS output"
```

---

### Task 3: Public Proxy QA Table and Chart

**Files:**
- Create: `src/economics/proxy_qa.py`
- Create: `scripts/build_cps_public_proxy_qa.py`
- Create: `tests/test_cps_public_proxy_qa.py`
- Modify: `src/economics/__init__.py`

**Interfaces:**
- Consumes:
  - `economics.charts.plot_multiple_series(df, value_col, title, ylabel, output_path) -> tuple[Figure, Axes]`
  - `economics.loaders.CBO_PROXY_VALUE_COL`
  - processed CSV files under a configurable processed directory
- Produces:
  - `build_indexed_common_overlap(series_frames: Mapping[str, pd.DataFrame]) -> pd.DataFrame`
  - `load_cps_public_proxy_series(processed_dir: str | Path) -> dict[str, pd.DataFrame]`
  - CLI: `python scripts/build_cps_public_proxy_qa.py`
  - CLI args: `--processed-dir`, `--table-out`, `--chart-out`

- [ ] **Step 1: Write failing QA tests**

Create `tests/test_cps_public_proxy_qa.py` with:

```python
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest

from economics.paths import repo_root
from economics.proxy_qa import build_indexed_common_overlap


def test_build_indexed_common_overlap_indexes_every_series_to_common_start() -> None:
    frames = {
        "Series A": pd.DataFrame({"year": [2000, 2001, 2002], "value": [50.0, 100.0, 110.0]}),
        "Series B": pd.DataFrame({"year": [2001, 2002, 2003], "value": [80.0, 120.0, 160.0]}),
    }

    out = build_indexed_common_overlap(frames)

    assert out.to_dict("records") == [
        {
            "year": 2001,
            "series": "Series A",
            "value": 100.0,
            "index_value": 100.0,
            "common_start_year": 2001,
            "common_end_year": 2002,
        },
        {
            "year": 2002,
            "series": "Series A",
            "value": 110.0,
            "index_value": 110.0,
            "common_start_year": 2001,
            "common_end_year": 2002,
        },
        {
            "year": 2001,
            "series": "Series B",
            "value": 80.0,
            "index_value": 100.0,
            "common_start_year": 2001,
            "common_end_year": 2002,
        },
        {
            "year": 2002,
            "series": "Series B",
            "value": 120.0,
            "index_value": 150.0,
            "common_start_year": 2001,
            "common_end_year": 2002,
        },
    ]


def test_build_indexed_common_overlap_rejects_no_common_overlap() -> None:
    frames = {
        "Series A": pd.DataFrame({"year": [2000], "value": [50.0]}),
        "Series B": pd.DataFrame({"year": [2001], "value": [80.0]}),
    }

    with pytest.raises(ValueError, match="No common overlap exists across the supplied series"):
        build_indexed_common_overlap(frames)


def test_build_cps_public_proxy_qa_script_writes_table_and_chart(tmp_path: Path) -> None:
    processed_dir = tmp_path / "processed"
    table_out = tmp_path / "qa.csv"
    chart_out = tmp_path / "qa.png"
    processed_dir.mkdir()

    (processed_dir / "cps_ipums_median_adult_equivalent_resources_real.csv").write_text(
        "\n".join(
            [
                "year,value,nominal_value,price_index,real_base_year,series,source,"
                "variant,include_capital_gains,include_health_insurance,population,notes",
                "2021,100.0,90.0,90.0,2024,"
                "Median adult-equivalent disposable resources,fixture,cps,False,False,"
                "all,fixture",
                "2022,110.0,105.0,95.0,2024,"
                "Median adult-equivalent disposable resources,fixture,cps,False,False,"
                "all,fixture",
            ]
        )
        + "\n"
    )
    (processed_dir / "cbo_proxy_median_adjusted_income_after_tax_transfer.csv").write_text(
        "year,median_adjusted_income_after_transfers_taxes_2022_dollars,source,notes\n"
        "2021,200.0,fixture,fixture\n"
        "2022,220.0,fixture,fixture\n"
    )
    for filename, series_name, start, end in [
        ("fred_real_median_personal_income.csv", "Real median personal income", 50.0, 55.0),
        ("fred_real_median_household_income.csv", "Real median household income", 80.0, 84.0),
        (
            "fred_real_disposable_personal_income_per_capita.csv",
            "Real disposable personal income per capita",
            70.0,
            77.0,
        ),
    ]:
        (processed_dir / filename).write_text(
            "year,value,series_id,series,source,notes\n"
            f"2021,{start},TEST,{series_name},fixture,fixture\n"
            f"2022,{end},TEST,{series_name},fixture,fixture\n"
        )

    result = subprocess.run(
        [
            sys.executable,
            str(repo_root() / "scripts" / "build_cps_public_proxy_qa.py"),
            "--processed-dir",
            str(processed_dir),
            "--table-out",
            str(table_out),
            "--chart-out",
            str(chart_out),
        ],
        cwd=repo_root(),
        check=True,
        capture_output=True,
        text=True,
    )

    table = pd.read_csv(table_out)

    assert f"Wrote 10 QA rows to {table_out}" in result.stdout
    assert f"Saved QA chart to {chart_out}" in result.stdout
    assert chart_out.exists()
    assert list(table.columns) == [
        "year",
        "series",
        "value",
        "index_value",
        "common_start_year",
        "common_end_year",
    ]
    assert set(table["series"]) == {
        "CBO adjusted income after transfers and taxes",
        "Median adult-equivalent disposable resources",
        "Real disposable personal income per capita",
        "Real median household income",
        "Real median personal income",
    }
    assert table["common_start_year"].unique().tolist() == [2021]
    assert table["common_end_year"].unique().tolist() == [2022]
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
FF_TMPDIR=/tmp TMPDIR=/tmp TMP=/tmp TEMP=/tmp ./.venv/bin/python -m pytest tests/test_cps_public_proxy_qa.py -q
```

Expected: FAIL during collection with `ModuleNotFoundError: No module named 'economics.proxy_qa'`.

- [ ] **Step 3: Add the QA helper module**

Create `src/economics/proxy_qa.py` with:

```python
"""QA helpers for comparing CPS/IPUMS output to public proxy series."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

import pandas as pd

from economics.loaders import CBO_PROXY_VALUE_COL, load_cbo_proxy

CPS_REAL_FILENAME = "cps_ipums_median_adult_equivalent_resources_real.csv"
CBO_PROXY_FILENAME = "cbo_proxy_median_adjusted_income_after_tax_transfer.csv"
FRED_COMPARISON_FILENAMES = (
    "fred_real_median_personal_income.csv",
    "fred_real_median_household_income.csv",
    "fred_real_disposable_personal_income_per_capita.csv",
)


def build_indexed_common_overlap(
    series_frames: Mapping[str, pd.DataFrame],
    *,
    value_col: str = "value",
    year_col: str = "year",
) -> pd.DataFrame:
    """Return tidy indexed rows for the common overlap across all series."""

    if not series_frames:
        raise ValueError("At least one series is required")

    common_years: set[int] | None = None
    normalized_frames: dict[str, pd.DataFrame] = {}
    for series, df in series_frames.items():
        frame = df[[year_col, value_col]].copy()
        frame[year_col] = pd.to_numeric(frame[year_col], errors="coerce")
        frame[value_col] = pd.to_numeric(frame[value_col], errors="coerce")
        frame = frame.dropna(subset=[year_col, value_col]).copy()
        frame[year_col] = frame[year_col].astype(int)
        frame = frame.sort_values(year_col).drop_duplicates(year_col, keep="last")
        normalized_frames[series] = frame

        years = set(frame[year_col])
        common_years = years if common_years is None else common_years.intersection(years)

    if not common_years:
        raise ValueError("No common overlap exists across the supplied series")

    common_start_year = min(common_years)
    common_end_year = max(common_years)
    rows: list[pd.DataFrame] = []
    for series, frame in normalized_frames.items():
        overlap = frame[
            (frame[year_col] >= common_start_year)
            & (frame[year_col] <= common_end_year)
            & frame[year_col].isin(common_years)
        ].copy()
        base_value = float(overlap.loc[overlap[year_col] == common_start_year, value_col].iloc[0])
        overlap["series"] = series
        overlap["index_value"] = overlap[value_col] / base_value * 100
        overlap["common_start_year"] = common_start_year
        overlap["common_end_year"] = common_end_year
        rows.append(
            overlap.rename(columns={year_col: "year", value_col: "value"})[
                [
                    "year",
                    "series",
                    "value",
                    "index_value",
                    "common_start_year",
                    "common_end_year",
                ]
            ]
        )

    return pd.concat(rows, ignore_index=True).sort_values(["series", "year"]).reset_index(drop=True)


def load_cps_public_proxy_series(processed_dir: str | Path) -> dict[str, pd.DataFrame]:
    """Load CPS real output plus CBO and FRED processed comparison files."""

    processed_dir = Path(processed_dir)
    cps = pd.read_csv(processed_dir / CPS_REAL_FILENAME)
    series_frames = {
        str(cps["series"].iloc[0]): cps[["year", "value"]],
    }

    cbo = load_cbo_proxy(processed_dir / CBO_PROXY_FILENAME)
    series_frames["CBO adjusted income after transfers and taxes"] = cbo[
        ["year", CBO_PROXY_VALUE_COL]
    ].rename(columns={CBO_PROXY_VALUE_COL: "value"})

    for filename in FRED_COMPARISON_FILENAMES:
        df = pd.read_csv(processed_dir / filename)
        series_frames[str(df["series"].iloc[0])] = df[["year", "value"]]

    return series_frames
```

- [ ] **Step 4: Add the QA script**

Create `scripts/build_cps_public_proxy_qa.py` with:

```python
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
```

- [ ] **Step 5: Export QA helpers**

Modify `src/economics/__init__.py` by adding:

```python
from economics.proxy_qa import build_indexed_common_overlap, load_cps_public_proxy_series
```

Add these names to `__all__`:

```python
    "build_indexed_common_overlap",
    "load_cps_public_proxy_series",
```

- [ ] **Step 6: Run focused QA tests**

Run:

```bash
FF_TMPDIR=/tmp TMPDIR=/tmp TMP=/tmp TEMP=/tmp ./.venv/bin/python -m pytest tests/test_cps_public_proxy_qa.py -q
```

Expected: PASS with `3 passed`.

- [ ] **Step 7: Run all new phase tests**

Run:

```bash
FF_TMPDIR=/tmp TMPDIR=/tmp TMP=/tmp TEMP=/tmp ./.venv/bin/python -m pytest tests/test_prices.py tests/test_cps_ipums_real.py tests/test_cps_public_proxy_qa.py -q
```

Expected: PASS with `15 passed`.

- [ ] **Step 8: Commit Task 3**

Run:

```bash
git add src/economics/proxy_qa.py src/economics/__init__.py scripts/build_cps_public_proxy_qa.py tests/test_cps_public_proxy_qa.py
git commit -m "feat: add CPS public proxy QA outputs"
```

---

### Task 4: Documentation and Final Validation

**Files:**
- Modify: `README.md`
- Modify: `docs/data_sources.md`
- Modify: `docs/methodology.md`
- Modify: `tests/test_notebook.py`

**Interfaces:**
- Consumes:
  - `scripts/build_cps_ipums_real.py`
  - `scripts/build_cps_public_proxy_qa.py`
  - documented paths from the approved spec
- Produces:
  - user-facing workflow documentation for annual price-index input, CPS real output, and QA artifacts
  - doc guardrails in `tests/test_notebook.py`

- [ ] **Step 1: Add failing documentation guardrail tests**

Modify `tests/test_notebook.py` by appending:

```python

def test_docs_document_cps_real_dollar_qa_workflow() -> None:
    readme = Path("README.md").read_text()
    data_sources = Path("docs/data_sources.md").read_text()
    methodology = Path("docs/methodology.md").read_text()

    assert "data/raw/annual_price_index.csv" in readme
    assert "scripts/build_cps_ipums_real.py" in readme
    assert "scripts/build_cps_public_proxy_qa.py" in readme
    assert "cps_ipums_median_adult_equivalent_resources_real.csv" in readme
    assert "annual_price_index.csv" in data_sources
    assert "year" in data_sources
    assert "price_index" in data_sources
    assert "nominal CPS/IPUMS" in methodology
    assert "real CPS/IPUMS" in methodology
    assert "indexed public-proxy QA" in methodology
```

- [ ] **Step 2: Run documentation test to verify it fails**

Run:

```bash
FF_TMPDIR=/tmp TMPDIR=/tmp TMP=/tmp TEMP=/tmp ./.venv/bin/python -m pytest tests/test_notebook.py::test_docs_document_cps_real_dollar_qa_workflow -q
```

Expected: FAIL because the README and docs do not yet include the new workflow strings.

- [ ] **Step 3: Update README source-file expectations**

In `README.md`, update the manual source-file list to include:

```text
data/raw/annual_price_index.csv
```

After the FRED comparison section, add:

````markdown
## Annual price index for CPS/IPUMS real dollars

The CPS/IPUMS microdata estimator first writes nominal annual medians. To
compare that trend with real public proxy series, manually provide an annual
price-index CSV at:

```text
data/raw/annual_price_index.csv
```

Required columns:

```text
year
price_index
```

The default real-dollar base year is 2024.
````

- [ ] **Step 4: Update README CPS workflow**

In `README.md`, after the CPS/IPUMS demo build instructions and before the attrition diagnostic section, add:

````markdown
Build the real-dollar CPS/IPUMS output after providing the annual price-index
file:

```bash
python scripts/build_cps_ipums_real.py
```

The script writes:

```text
data/processed/cps_ipums_median_adult_equivalent_resources_real.csv
```

The existing `data/processed/cps_ipums_median_adult_equivalent_resources.csv`
file remains the nominal CPS/IPUMS output. The real output keeps
`nominal_value`, `price_index`, and `real_base_year` columns so the inflation
adjustment is auditable.
````

- [ ] **Step 5: Update README QA workflow**

In `README.md`, after the public proxy summary or CPS real output text, add:

````markdown
## Build the CPS/IPUMS public-proxy QA artifacts

After building the real CPS/IPUMS output, run:

```bash
python scripts/build_cps_public_proxy_qa.py
```

The script writes:

```text
outputs/tables/cps_public_proxy_qa_summary.csv
outputs/charts/cps_public_proxy_indexed_comparison.png
```

These QA artifacts index CPS/IPUMS, CBO, and FRED public proxy series to the
first shared year. They are diagnostics for trend plausibility, not final
publication charts.
````

- [ ] **Step 6: Update data source documentation**

In `docs/data_sources.md`, add a section before `## CPS ASEC / IPUMS CPS`:

````markdown
## Annual price index

Project use:

Converts nominal CPS/IPUMS annual median resources into base-year real dollars.
The project keeps the price-index input manual so the chosen deflator remains
explicit.

Expected manual file:

```text
data/raw/annual_price_index.csv
```

Required columns:

```text
year
price_index
```

Optional metadata columns such as `series_id`, `series`, `source`, and `notes`
may be present. The current builder requires only `year` and `price_index`.
The default real-dollar base year is 2024.
````

- [ ] **Step 7: Update methodology documentation**

In `docs/methodology.md`, add this paragraph to the CPS/IPUMS estimator boundary section:

````markdown
The starter CPS/IPUMS estimator writes a nominal CPS/IPUMS annual median first.
That nominal output should not be compared directly with real CBO or FRED
series. The real CPS/IPUMS build applies the documented annual price index and
writes a separate real-dollar file with `nominal_value`, `price_index`, and
`real_base_year` audit columns.

The indexed public-proxy QA table and chart compare the real CPS/IPUMS series
with CBO and FRED series over their common overlap window, indexing each series
to the first shared year. This fixes inflation comparability for trend QA, but
it does not resolve the remaining resource-concept limits around noncash
benefits, health-insurance value, and reviewed resource-unit treatment.
````

- [ ] **Step 8: Run documentation guardrail tests**

Run:

```bash
FF_TMPDIR=/tmp TMPDIR=/tmp TMP=/tmp TEMP=/tmp ./.venv/bin/python -m pytest tests/test_notebook.py -q
```

Expected: PASS.

- [ ] **Step 9: Run full automated validation**

Run:

```bash
FF_TMPDIR=/tmp TMPDIR=/tmp TMP=/tmp TEMP=/tmp ./.venv/bin/python -m pytest -q
./.venv/bin/python -m ruff check .
git diff --check
```

Expected:

- pytest: PASS.
- ruff: `All checks passed!`
- `git diff --check`: no output.

- [ ] **Step 10: Run local real-build smoke check when price index exists**

Run:

```bash
if [ -f data/raw/annual_price_index.csv ]; then
  ./.venv/bin/python scripts/build_cps_ipums_real.py
  ./.venv/bin/python scripts/build_cps_public_proxy_qa.py
  ./.venv/bin/python - <<'PY'
import pandas as pd

real = pd.read_csv("data/processed/cps_ipums_median_adult_equivalent_resources_real.csv")
qa = pd.read_csv("outputs/tables/cps_public_proxy_qa_summary.csv")
cols = ["year", "value", "nominal_value", "price_index", "real_base_year"]
print(real[cols].head().to_string(index=False))
print(real[cols].tail().to_string(index=False))
print(qa.groupby("series")["year"].agg(["min", "max", "count"]).to_string())
PY
else
  echo "Skipping local real-build smoke check because data/raw/annual_price_index.csv is absent"
fi
```

Expected when the price-index file is absent:

```text
Skipping local real-build smoke check because data/raw/annual_price_index.csv is absent
```

Expected when the price-index file is present:

- `scripts/build_cps_ipums_real.py` writes `data/processed/cps_ipums_median_adult_equivalent_resources_real.csv`.
- `scripts/build_cps_public_proxy_qa.py` writes `outputs/tables/cps_public_proxy_qa_summary.csv` and `outputs/charts/cps_public_proxy_indexed_comparison.png`.
- The printed QA group summary shows the same common start and end year for all five series.

- [ ] **Step 11: Commit Task 4**

Run:

```bash
git add README.md docs/data_sources.md docs/methodology.md tests/test_notebook.py
git commit -m "docs: document CPS real-dollar QA workflow"
```

---

## Final Verification

After all tasks are complete, run:

```bash
git status --short --branch
FF_TMPDIR=/tmp TMPDIR=/tmp TMP=/tmp TEMP=/tmp ./.venv/bin/python -m pytest tests/test_prices.py tests/test_cps_ipums_real.py tests/test_cps_public_proxy_qa.py -q
FF_TMPDIR=/tmp TMPDIR=/tmp TMP=/tmp TEMP=/tmp ./.venv/bin/python -m pytest -q
./.venv/bin/python -m ruff check .
git diff --check
```

Expected:

- `git status --short --branch` shows only expected branch-ahead status and no unstaged changes.
- Focused phase tests pass.
- Full pytest passes.
- Ruff reports `All checks passed!`.
- `git diff --check` prints no whitespace errors.

If `data/raw/annual_price_index.csv` exists, also run:

```bash
./.venv/bin/python scripts/build_cps_ipums_real.py
./.venv/bin/python scripts/build_cps_public_proxy_qa.py
```

Expected:

- `data/processed/cps_ipums_median_adult_equivalent_resources_real.csv` exists.
- `outputs/tables/cps_public_proxy_qa_summary.csv` exists.
- `outputs/charts/cps_public_proxy_indexed_comparison.png` exists.
