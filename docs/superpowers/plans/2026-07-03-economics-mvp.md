# Economics MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the existing economics starter scaffold into a testable Python package with public proxy loaders, adult-equivalence/resource metrics, chart/table helpers, documentation, and a starter notebook.

**Architecture:** Keep the current project lightweight and transparent. Split the existing `metrics.py` behavior into focused modules under `src/economics/`, keep `metrics.py` as a compatibility facade, and wire scripts/notebooks through package APIs. External datasets remain manually supplied files under `data/raw/`; bundled processed data is clearly labeled as a starter CBO proxy pending official workbook verification.

**Tech Stack:** Python 3.11+, pandas, matplotlib, pathlib, pytest, Jupyter notebook JSON.

## Global Constraints

- Extend the existing starter scaffold rather than replacing it.
- Do not hard-code fragile absolute file paths.
- Use `str | Path` inputs for file paths and resolve paths at call sites.
- Raise `ValueError` with missing column names when a file does not match the expected schema.
- Keep the bundled CBO proxy data labeled as starter data that must be verified against the official CBO supplemental workbook before publication.
- Do not download external datasets automatically.
- Do not implement the CPS/IPUMS microdata estimator in this MVP.
- Keep implementation small, readable, modular, and well-commented.

---

## File Structure

- Create `pyproject.toml`: package metadata, dependencies, pytest config, editable-install support.
- Modify `.gitignore`: add notebook checkpoints and table output patterns if missing.
- Create `src/economics/equivalence.py`: square-root equivalence scale and household-resource adjustment.
- Create `src/economics/resources.py`: `ResourceComponents` dataclass and broad resource arithmetic.
- Create `src/economics/series.py`: weighted median, real-dollar helper, growth columns, series summaries.
- Modify `src/economics/metrics.py`: re-export core APIs for compatibility with the current script.
- Modify `src/economics/__init__.py`: expose stable public helpers.
- Create `src/economics/paths.py`: repo-relative path helpers.
- Create `src/economics/loaders.py`: CBO proxy and generic comparison-series CSV loaders.
- Create `src/economics/charts.py`: matplotlib plotting helper.
- Create `src/economics/tables.py`: compact summary-table helper.
- Modify `scripts/plot_cbo_proxy.py`: use loaders/charts/tables helpers.
- Modify `README.md`: document package install, structure, data workflow, and commands.
- Modify `docs/methodology.md`: tighten limitations and comparison metric framing.
- Modify `docs/data_sources.md`: document exact expected manual raw filenames and columns.
- Create `notebooks/01_cbo_proxy_starter.ipynb`: executable starter notebook.
- Create `tests/test_core_metrics.py`: equivalence, resource, weighted median, real-dollar, growth, summary tests.
- Create `tests/test_loaders.py`: schema checks and comparison loader tests.
- Create `tests/test_outputs.py`: chart/table/script-facing helper tests.
- Create `tests/test_notebook.py`: notebook existence and starter-data caveat checks.

---

### Task 1: Package Config And Core Metric Modules

**Files:**
- Create: `pyproject.toml`
- Create: `tests/test_core_metrics.py`
- Create: `src/economics/equivalence.py`
- Create: `src/economics/resources.py`
- Create: `src/economics/series.py`
- Modify: `src/economics/metrics.py`
- Modify: `src/economics/__init__.py`
- Modify: `.gitignore`

**Interfaces:**
- Consumes: existing `src/economics/metrics.py` functions and `data/processed/cbo_proxy_median_adjusted_income_after_tax_transfer.csv`.
- Produces:
  - `square_root_equivalence_scale(household_size: float) -> float`
  - `equivalize_resources(resources: float, household_size: float) -> float`
  - `ResourceComponents.comprehensive_disposable_resources() -> float`
  - `weighted_median(values: Iterable[float], weights: Iterable[float]) -> float`
  - `real_value(nominal_value: float, price_index: float, base_price_index: float) -> float`
  - `add_growth_columns(df: pd.DataFrame, value_col: str, year_col: str = "year") -> pd.DataFrame`
  - `summarize_series(df: pd.DataFrame, value_col: str, year_col: str = "year") -> dict[str, float]`
  - compatibility `load_cbo_proxy(path: str | Path) -> pd.DataFrame` remains available from `economics.metrics`

- [ ] **Step 1: Add package/test config**

Create `pyproject.toml`:

```toml
[build-system]
requires = ["setuptools>=68", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "economics"
version = "0.1.0"
description = "Transparent time-series measures of US median adult-equivalent disposable resources."
readme = "README.md"
requires-python = ">=3.11"
dependencies = [
    "matplotlib>=3.8",
    "pandas>=2.0",
]

[project.optional-dependencies]
dev = [
    "jupyter>=1.0",
    "nbformat>=5.9",
    "pytest>=8.0",
    "ruff>=0.5",
]

[tool.setuptools.packages.find]
where = ["src"]

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src"]

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I", "B"]
```

Modify `.gitignore` so it includes:

```gitignore
# Notebooks
.ipynb_checkpoints/
notebooks/.ipynb_checkpoints/
```

Run:

```bash
python -m pip install -e ".[dev]"
```

Expected: editable install completes, or reports already-satisfied dependencies.

- [ ] **Step 2: Write failing core metric tests**

Create `tests/test_core_metrics.py`:

```python
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
```

- [ ] **Step 3: Run tests to verify they fail for missing split modules**

Run:

```bash
python -m pytest tests/test_core_metrics.py -q
```

Expected: FAIL with `ModuleNotFoundError` for `economics.equivalence`, `economics.resources`, or `economics.series`.

- [ ] **Step 4: Implement core metric modules**

Create `src/economics/equivalence.py`:

```python
"""Household-size equivalence-scale helpers."""

from __future__ import annotations

from math import sqrt


def square_root_equivalence_scale(household_size: float) -> float:
    """Return the square-root equivalence scale for a household.

    The scale treats shared living costs as partly joint: a larger household
    needs more resources than a one-person household, but less than a strict
    per-capita multiple.
    """

    if household_size <= 0:
        raise ValueError("household_size must be positive")
    return sqrt(household_size)


def equivalize_resources(resources: float, household_size: float) -> float:
    """Adjust household resources for household size."""

    return resources / square_root_equivalence_scale(household_size)
```

Create `src/economics/resources.py`:

```python
"""Disposable-resource component helpers."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ResourceComponents:
    """Components of a broad disposable-resource measure.

    Amounts should be expressed in the same dollar year before combining.
    """

    money_income: float = 0.0
    realized_capital_gains: float = 0.0
    noncash_benefits: float = 0.0
    health_insurance_value: float = 0.0
    federal_income_taxes: float = 0.0
    payroll_taxes: float = 0.0
    state_local_income_taxes: float = 0.0

    def comprehensive_disposable_resources(self) -> float:
        """Return broad household resources after taxes."""

        resources = (
            self.money_income
            + self.realized_capital_gains
            + self.noncash_benefits
            + self.health_insurance_value
        )
        taxes = (
            self.federal_income_taxes
            + self.payroll_taxes
            + self.state_local_income_taxes
        )
        return resources - taxes
```

Create `src/economics/series.py`:

```python
"""Time-series and weighted-statistic helpers."""

from __future__ import annotations

from collections.abc import Iterable

import pandas as pd


def weighted_median(values: Iterable[float], weights: Iterable[float]) -> float:
    """Calculate a weighted median from values and observation weights."""

    df = pd.DataFrame({"value": list(values), "weight": list(weights)})
    df = df.dropna(subset=["value", "weight"])
    df = df[df["weight"] > 0]

    if df.empty:
        raise ValueError("No positive-weight observations were supplied")

    df = df.sort_values("value").reset_index(drop=True)
    cutoff = df["weight"].sum() / 2
    cumulative_weight = df["weight"].cumsum()

    return float(df.loc[cumulative_weight >= cutoff, "value"].iloc[0])


def real_value(nominal_value: float, price_index: float, base_price_index: float) -> float:
    """Convert a nominal amount to base-period real dollars."""

    if price_index <= 0:
        raise ValueError("price_index must be positive")
    if base_price_index <= 0:
        raise ValueError("base_price_index must be positive")
    return nominal_value * base_price_index / price_index


def add_growth_columns(
    df: pd.DataFrame,
    value_col: str,
    year_col: str = "year",
) -> pd.DataFrame:
    """Add one-year, cumulative, and annualized growth columns."""

    out = df.sort_values(year_col).copy()
    first_value = out[value_col].iloc[0]
    first_year = out[year_col].iloc[0]

    out[f"{value_col}_yoy_pct"] = out[value_col].pct_change() * 100
    out[f"{value_col}_cumulative_pct"] = (out[value_col] / first_value - 1) * 100

    years_elapsed = out[year_col] - first_year
    out[f"{value_col}_annualized_pct"] = (
        (out[value_col] / first_value) ** (1 / years_elapsed.replace(0, pd.NA)) - 1
    ) * 100

    return out


def summarize_series(
    df: pd.DataFrame,
    value_col: str,
    year_col: str = "year",
) -> dict[str, float]:
    """Return a compact start/end/growth summary for a time series."""

    ordered = df.sort_values(year_col)
    first = ordered.iloc[0]
    last = ordered.iloc[-1]

    years = float(last[year_col] - first[year_col])
    cumulative_growth = float(last[value_col] / first[value_col] - 1)

    if years <= 0:
        annualized_growth = float("nan")
    else:
        annualized_growth = float((last[value_col] / first[value_col]) ** (1 / years) - 1)

    return {
        "start_year": int(first[year_col]),
        "end_year": int(last[year_col]),
        "start_value": float(first[value_col]),
        "end_value": float(last[value_col]),
        "cumulative_growth_pct": cumulative_growth * 100,
        "annualized_growth_pct": annualized_growth * 100,
    }
```

Replace `src/economics/metrics.py` with:

```python
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
```

Replace `src/economics/__init__.py` with:

```python
"""Economics data-project package."""

from economics.equivalence import equivalize_resources, square_root_equivalence_scale
from economics.resources import ResourceComponents
from economics.series import add_growth_columns, real_value, summarize_series, weighted_median

__all__ = [
    "ResourceComponents",
    "add_growth_columns",
    "equivalize_resources",
    "real_value",
    "square_root_equivalence_scale",
    "summarize_series",
    "weighted_median",
]
```

- [ ] **Step 5: Run tests to verify they pass**

Run:

```bash
python -m pytest tests/test_core_metrics.py -q
```

Expected: PASS.

- [ ] **Step 6: Commit Task 1**

Run:

```bash
git add .gitignore pyproject.toml src/economics/__init__.py src/economics/equivalence.py src/economics/metrics.py src/economics/resources.py src/economics/series.py tests/test_core_metrics.py
git commit -m "feat: add core economics metric helpers"
```

Expected: commit succeeds.

---

### Task 2: Repo Paths And Source Loaders

**Files:**
- Create: `tests/test_loaders.py`
- Create: `src/economics/paths.py`
- Create: `src/economics/loaders.py`
- Modify: `src/economics/metrics.py`
- Modify: `src/economics/__init__.py`

**Interfaces:**
- Consumes:
  - `data/processed/cbo_proxy_median_adjusted_income_after_tax_transfer.csv`
  - `summarize_series()` and growth helpers from Task 1.
- Produces:
  - `CBO_PROXY_VALUE_COL: str`
  - `SourceFileSpec`
  - `repo_root() -> Path`
  - `data_path(*parts: str) -> Path`
  - `raw_data_path(*parts: str) -> Path`
  - `processed_data_path(*parts: str) -> Path`
  - `output_path(*parts: str) -> Path`
  - `validate_required_columns(df: pd.DataFrame, required_columns: Iterable[str], source_label: str) -> None`
  - `load_cbo_proxy(path: str | Path) -> pd.DataFrame`
  - `load_comparison_series(path: str | Path, value_col: str = "value", year_col: str = "year", series_name: str | None = None) -> pd.DataFrame`

- [ ] **Step 1: Write failing loader tests**

Create `tests/test_loaders.py`:

```python
from pathlib import Path

import pandas as pd
import pytest

from economics.loaders import (
    CBO_PROXY_VALUE_COL,
    load_cbo_proxy,
    load_comparison_series,
    validate_required_columns,
)
from economics.paths import processed_data_path, repo_root


def test_repo_root_points_to_project_directory() -> None:
    assert (repo_root() / "README.md").exists()


def test_processed_data_path_builds_repo_relative_path() -> None:
    path = processed_data_path("cbo_proxy_median_adjusted_income_after_tax_transfer.csv")
    assert path == repo_root() / "data" / "processed" / path.name


def test_validate_required_columns_reports_missing_columns() -> None:
    df = pd.DataFrame({"year": [2020]})

    with pytest.raises(ValueError, match="starter file missing required columns: \\['value'\\]"):
        validate_required_columns(df, ["year", "value"], "starter file")


def test_load_cbo_proxy_reads_bundled_starter_series() -> None:
    path = processed_data_path("cbo_proxy_median_adjusted_income_after_tax_transfer.csv")

    df = load_cbo_proxy(path)

    assert list(df.columns[:2]) == ["year", CBO_PROXY_VALUE_COL]
    assert df["year"].iloc[0] == 1979
    assert df["year"].iloc[-1] == 2022


def test_load_cbo_proxy_rejects_missing_value_column(tmp_path: Path) -> None:
    bad_path = tmp_path / "bad_cbo.csv"
    pd.DataFrame({"year": [2020], "wrong": [1]}).to_csv(bad_path, index=False)

    with pytest.raises(ValueError, match=CBO_PROXY_VALUE_COL):
        load_cbo_proxy(bad_path)


def test_load_comparison_series_normalizes_to_year_value_and_series(tmp_path: Path) -> None:
    path = tmp_path / "comparison.csv"
    pd.DataFrame({"year": [2021, 2020], "median": [12, 10]}).to_csv(path, index=False)

    df = load_comparison_series(path, value_col="median", series_name="Real median test")

    assert df.to_dict("records") == [
        {"year": 2020, "value": 10, "series": "Real median test"},
        {"year": 2021, "value": 12, "series": "Real median test"},
    ]
```

- [ ] **Step 2: Run tests to verify they fail for missing modules**

Run:

```bash
python -m pytest tests/test_loaders.py -q
```

Expected: FAIL with `ModuleNotFoundError` for `economics.loaders` or `economics.paths`.

- [ ] **Step 3: Implement path and loader modules**

Create `src/economics/paths.py`:

```python
"""Repository-relative path helpers."""

from __future__ import annotations

from pathlib import Path


def repo_root() -> Path:
    """Return the repository root based on the installed source location."""

    return Path(__file__).resolve().parents[2]


def data_path(*parts: str) -> Path:
    """Return a path under the repo's data directory."""

    return repo_root() / "data" / Path(*parts)


def raw_data_path(*parts: str) -> Path:
    """Return a path under data/raw."""

    return data_path("raw", *parts)


def processed_data_path(*parts: str) -> Path:
    """Return a path under data/processed."""

    return data_path("processed", *parts)


def output_path(*parts: str) -> Path:
    """Return a path under outputs."""

    return repo_root() / "outputs" / Path(*parts)
```

Create `src/economics/loaders.py`:

```python
"""CSV loaders for public proxy and comparison series."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

import pandas as pd


CBO_PROXY_VALUE_COL = "median_adjusted_income_after_transfers_taxes_2022_dollars"


@dataclass(frozen=True)
class SourceFileSpec:
    """Manual source-file contract for a public data series."""

    file_name: str
    required_columns: tuple[str, ...]
    description: str


RAW_SOURCE_FILE_SPECS: dict[str, SourceFileSpec] = {
    "cbo_distribution_household_income_2022": SourceFileSpec(
        file_name="cbo_distribution_household_income_2022.csv",
        required_columns=("year", CBO_PROXY_VALUE_COL),
        description="CBO adjusted household income after transfers and federal taxes.",
    ),
    "fred_real_median_personal_income": SourceFileSpec(
        file_name="fred_real_median_personal_income.csv",
        required_columns=("year", "value"),
        description="FRED/Census real median personal income comparison series.",
    ),
    "fred_real_median_household_income": SourceFileSpec(
        file_name="fred_real_median_household_income.csv",
        required_columns=("year", "value"),
        description="FRED/Census real median household income comparison series.",
    ),
    "fred_real_disposable_personal_income_per_capita": SourceFileSpec(
        file_name="fred_real_disposable_personal_income_per_capita.csv",
        required_columns=("year", "value"),
        description="FRED/BEA real disposable personal income per capita comparison series.",
    ),
}


def validate_required_columns(
    df: pd.DataFrame,
    required_columns: Iterable[str],
    source_label: str,
) -> None:
    """Raise a clear error if a DataFrame lacks required columns."""

    missing = sorted(set(required_columns).difference(df.columns))
    if missing:
        raise ValueError(f"{source_label} missing required columns: {missing}")


def load_cbo_proxy(path: str | Path) -> pd.DataFrame:
    """Load the starter CBO proxy CSV and sort it by year."""

    path = Path(path)
    df = pd.read_csv(path)
    validate_required_columns(df, ["year", CBO_PROXY_VALUE_COL], str(path))
    return df.sort_values("year").reset_index(drop=True)


def load_comparison_series(
    path: str | Path,
    value_col: str = "value",
    year_col: str = "year",
    series_name: str | None = None,
) -> pd.DataFrame:
    """Load a simple annual comparison series as year/value/series columns."""

    path = Path(path)
    df = pd.read_csv(path)
    validate_required_columns(df, [year_col, value_col], str(path))

    out = df[[year_col, value_col]].rename(columns={year_col: "year", value_col: "value"})
    if series_name is not None:
        out["series"] = series_name
    return out.sort_values("year").reset_index(drop=True)
```

Modify `src/economics/metrics.py` to include loader exports:

```python
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
```

Modify `src/economics/__init__.py` to include loader exports:

```python
"""Economics data-project package."""

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
```

- [ ] **Step 4: Run loader tests**

Run:

```bash
python -m pytest tests/test_loaders.py -q
```

Expected: PASS.

- [ ] **Step 5: Run core tests again**

Run:

```bash
python -m pytest tests/test_core_metrics.py tests/test_loaders.py -q
```

Expected: PASS.

- [ ] **Step 6: Commit Task 2**

Run:

```bash
git add src/economics/__init__.py src/economics/loaders.py src/economics/metrics.py src/economics/paths.py tests/test_loaders.py
git commit -m "feat: add public data loaders"
```

Expected: commit succeeds.

---

### Task 3: Chart And Summary Table Helpers

**Files:**
- Create: `tests/test_outputs.py`
- Create: `src/economics/charts.py`
- Create: `src/economics/tables.py`
- Modify: `scripts/plot_cbo_proxy.py`

**Interfaces:**
- Consumes:
  - `load_cbo_proxy(path) -> pd.DataFrame`
  - `add_growth_columns(df, value_col)`
  - `summarize_series(df, value_col)`
  - `CBO_PROXY_VALUE_COL`
- Produces:
  - `plot_time_series(df, value_col, *, year_col="year", title, ylabel, output_path=None) -> tuple[Figure, Axes]`
  - `build_summary_table(df, value_col, *, label, year_col="year") -> pd.DataFrame`

- [ ] **Step 1: Write failing output-helper tests**

Create `tests/test_outputs.py`:

```python
from pathlib import Path

import pandas as pd
import pytest

from economics.charts import plot_time_series
from economics.tables import build_summary_table


def test_build_summary_table_returns_named_metric_rows() -> None:
    df = pd.DataFrame({"year": [2000, 2002], "value": [100, 121]})

    table = build_summary_table(df, "value", label="Test series")
    records = table.to_dict("records")

    assert records[:5] == [
        {"series": "Test series", "metric": "start_year", "value": 2000.0},
        {"series": "Test series", "metric": "end_year", "value": 2002.0},
        {"series": "Test series", "metric": "start_value", "value": 100.0},
        {"series": "Test series", "metric": "end_value", "value": 121.0},
        {"series": "Test series", "metric": "cumulative_growth_pct", "value": 21.0},
    ]
    assert records[5] == {
        "series": "Test series",
        "metric": "annualized_growth_pct",
        "value": pytest.approx(10.0),
    }


def test_plot_time_series_writes_chart_file(tmp_path: Path) -> None:
    df = pd.DataFrame({"year": [2000, 2001], "value": [100, 105]})
    output_path = tmp_path / "chart.png"

    fig, ax = plot_time_series(
        df,
        "value",
        title="Test title",
        ylabel="Test dollars",
        output_path=output_path,
    )

    assert output_path.exists()
    assert ax.get_title() == "Test title"
    assert ax.get_xlabel() == "Year"
    assert ax.get_ylabel() == "Test dollars"
    fig.clear()
```

- [ ] **Step 2: Run tests to verify they fail for missing modules**

Run:

```bash
python -m pytest tests/test_outputs.py -q
```

Expected: FAIL with `ModuleNotFoundError` for `economics.charts` or `economics.tables`.

- [ ] **Step 3: Implement chart and table modules**

Create `src/economics/tables.py`:

```python
"""Summary-table helpers."""

from __future__ import annotations

import pandas as pd

from economics.series import summarize_series


def build_summary_table(
    df: pd.DataFrame,
    value_col: str,
    *,
    label: str,
    year_col: str = "year",
) -> pd.DataFrame:
    """Return a long-form summary table for a time series."""

    summary = summarize_series(df, value_col, year_col=year_col)
    rows = [
        {"series": label, "metric": metric, "value": float(value)}
        for metric, value in summary.items()
    ]
    return pd.DataFrame(rows)
```

Create `src/economics/charts.py`:

```python
"""Matplotlib chart helpers for project time series."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.axes import Axes
from matplotlib.figure import Figure


def plot_time_series(
    df: pd.DataFrame,
    value_col: str,
    *,
    year_col: str = "year",
    title: str,
    ylabel: str,
    output_path: str | Path | None = None,
) -> tuple[Figure, Axes]:
    """Plot a single annual time series and optionally save it."""

    ordered = df.sort_values(year_col)
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(ordered[year_col], ordered[value_col], marker="o", linewidth=2)
    ax.set_title(title)
    ax.set_xlabel("Year")
    ax.set_ylabel(ylabel)
    ax.grid(True, axis="y", alpha=0.3)
    ax.yaxis.set_major_formatter(lambda x, pos: f"${x:,.0f}")

    fig.tight_layout()

    if output_path is not None:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(output_path, dpi=200)

    return fig, ax
```

- [ ] **Step 4: Run output-helper tests**

Run:

```bash
python -m pytest tests/test_outputs.py -q
```

Expected: PASS.

- [ ] **Step 5: Update the plotting script to use package helpers**

Replace `scripts/plot_cbo_proxy.py` with:

```python
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

from economics.charts import plot_time_series
from economics.loaders import CBO_PROXY_VALUE_COL, load_cbo_proxy
from economics.paths import output_path, processed_data_path
from economics.series import add_growth_columns
from economics.tables import build_summary_table


DATA_PATH = processed_data_path("cbo_proxy_median_adjusted_income_after_tax_transfer.csv")
OUTPUT_PATH = output_path("charts", "cbo_proxy_median_adjusted_income.png")


def main() -> None:
    df = load_cbo_proxy(DATA_PATH)
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
        output_path=OUTPUT_PATH,
    )
    plt.close(fig)
    print(f"Saved chart to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 6: Verify script output**

Run:

```bash
python scripts/plot_cbo_proxy.py
```

Expected: command prints a CBO proxy summary and `Saved chart to /home/mhpet/projects/economics/outputs/charts/cbo_proxy_median_adjusted_income.png`.

- [ ] **Step 7: Run all current tests**

Run:

```bash
python -m pytest tests/test_core_metrics.py tests/test_loaders.py tests/test_outputs.py -q
```

Expected: PASS.

- [ ] **Step 8: Commit Task 3**

Run:

```bash
git add scripts/plot_cbo_proxy.py src/economics/charts.py src/economics/tables.py tests/test_outputs.py
git commit -m "feat: add chart and table helpers"
```

Expected: commit succeeds.

---

### Task 4: Documentation, Manual Source Contracts, And Starter Notebook

**Files:**
- Create: `notebooks/01_cbo_proxy_starter.ipynb`
- Create: `tests/test_notebook.py`
- Modify: `README.md`
- Modify: `docs/methodology.md`
- Modify: `docs/data_sources.md`

**Interfaces:**
- Consumes:
  - `processed_data_path()`
  - `load_cbo_proxy()`
  - `CBO_PROXY_VALUE_COL`
  - `plot_time_series()`
  - `build_summary_table()`
- Produces:
  - documented repo structure and install commands,
  - exact manual raw data file contracts,
  - a notebook that loads bundled starter data and plots the CBO proxy.

- [ ] **Step 1: Write failing notebook/documentation tests**

Create `tests/test_notebook.py`:

```python
import json
from pathlib import Path


NOTEBOOK_PATH = Path("notebooks/01_cbo_proxy_starter.ipynb")


def test_starter_notebook_exists_and_mentions_cbo_proxy_caveat() -> None:
    notebook = json.loads(NOTEBOOK_PATH.read_text())
    text = "\n".join(
        "".join(cell.get("source", []))
        for cell in notebook["cells"]
        if cell.get("cell_type") == "markdown"
    )

    assert "starter proxy" in text
    assert "official CBO supplemental workbook" in text
    assert "not publication-ready" in text


def test_readme_documents_editable_install_and_notebook() -> None:
    readme = Path("README.md").read_text()

    assert 'pip install -e ".[dev]"' in readme
    assert "notebooks/01_cbo_proxy_starter.ipynb" in readme
    assert "data/raw/fred_real_median_personal_income.csv" in readme
```

- [ ] **Step 2: Run tests to verify they fail before notebook/docs update**

Run:

```bash
python -m pytest tests/test_notebook.py -q
```

Expected: FAIL because `notebooks/01_cbo_proxy_starter.ipynb` does not exist and README does not yet document the editable install/notebook/raw filenames.

- [ ] **Step 3: Create the starter notebook**

Create `notebooks/01_cbo_proxy_starter.ipynb`:

```json
{
  "cells": [
    {
      "cell_type": "markdown",
      "metadata": {},
      "source": [
        "# CBO Proxy Starter\n",
        "\n",
        "This notebook loads the bundled CBO starter proxy for median adjusted household income after transfers and federal taxes. The bundled series is a starter proxy, not publication-ready, and should be verified against the official CBO supplemental workbook before citation."
      ]
    },
    {
      "cell_type": "code",
      "execution_count": null,
      "metadata": {},
      "outputs": [],
      "source": [
        "from pathlib import Path\n",
        "import sys\n",
        "\n",
        "PROJECT_ROOT = Path.cwd()\n",
        "if not (PROJECT_ROOT / \"src\").exists():\n",
        "    PROJECT_ROOT = PROJECT_ROOT.parent\n",
        "\n",
        "src_path = PROJECT_ROOT / \"src\"\n",
        "if str(src_path) not in sys.path:\n",
        "    sys.path.insert(0, str(src_path))\n"
      ]
    },
    {
      "cell_type": "code",
      "execution_count": null,
      "metadata": {},
      "outputs": [],
      "source": [
        "from economics.charts import plot_time_series\n",
        "from economics.loaders import CBO_PROXY_VALUE_COL, load_cbo_proxy\n",
        "from economics.paths import processed_data_path\n",
        "from economics.series import add_growth_columns\n",
        "from economics.tables import build_summary_table\n"
      ]
    },
    {
      "cell_type": "code",
      "execution_count": null,
      "metadata": {},
      "outputs": [],
      "source": [
        "data_path = processed_data_path(\"cbo_proxy_median_adjusted_income_after_tax_transfer.csv\")\n",
        "cbo = load_cbo_proxy(data_path)\n",
        "cbo = add_growth_columns(cbo, CBO_PROXY_VALUE_COL)\n",
        "cbo.head()\n"
      ]
    },
    {
      "cell_type": "code",
      "execution_count": null,
      "metadata": {},
      "outputs": [],
      "source": [
        "summary = build_summary_table(\n",
        "    cbo,\n",
        "    CBO_PROXY_VALUE_COL,\n",
        "    label=\"CBO median adjusted income after transfers and federal taxes\",\n",
        ")\n",
        "summary\n"
      ]
    },
    {
      "cell_type": "code",
      "execution_count": null,
      "metadata": {},
      "outputs": [],
      "source": [
        "fig, ax = plot_time_series(\n",
        "    cbo,\n",
        "    CBO_PROXY_VALUE_COL,\n",
        "    title=\"Median adjusted income after transfers and federal taxes\",\n",
        "    ylabel=\"2022 dollars\",\n",
        ")\n",
        "fig\n"
      ]
    }
  ],
  "metadata": {
    "kernelspec": {
      "display_name": "Python 3",
      "language": "python",
      "name": "python3"
    },
    "language_info": {
      "name": "python",
      "pygments_lexer": "ipython3"
    }
  },
  "nbformat": 4,
  "nbformat_minor": 5
}
```

- [ ] **Step 4: Update README with install, structure, and data contracts**

Modify `README.md` so it contains these exact additions:

````markdown
## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Project structure

```text
data/raw/          manually downloaded source files
data/interim/      scratch transformations that are safe to regenerate
data/processed/    checked starter/proxy series used by scripts and notebooks
docs/              methodology and source notes
notebooks/         exploratory notebooks
outputs/charts/    generated chart images
outputs/tables/    generated summary tables
scripts/           command-line helpers
src/economics/     package code
tests/             focused pytest coverage
```

## Manual source-file expectations

External public datasets are not downloaded automatically. Put manually downloaded or exported files in these locations:

```text
data/raw/cbo_distribution_household_income_2022.csv
data/raw/fred_real_median_personal_income.csv
data/raw/fred_real_median_household_income.csv
data/raw/fred_real_disposable_personal_income_per_capita.csv
```

For the current loaders, each raw comparison CSV should include `year` and `value` columns. The starter CBO proxy uses `year` and `median_adjusted_income_after_transfers_taxes_2022_dollars`.

## Starter notebook

Open:

```text
notebooks/01_cbo_proxy_starter.ipynb
```

The notebook loads the bundled CBO starter proxy, prints a summary table, and plots the proxy metric. Treat the bundled CBO values as starter data until they are verified against the official CBO supplemental workbook.
````

- [ ] **Step 5: Update data source notes with raw filenames**

Modify `docs/data_sources.md` so the CBO/FRED sections include:

````markdown
Expected manual file:

```text
data/raw/cbo_distribution_household_income_2022.csv
```

Expected columns for project import:

```text
year
median_adjusted_income_after_transfers_taxes_2022_dollars
```
````

Modify each FRED comparison section so it includes its exact expected file:

```text
data/raw/fred_real_median_personal_income.csv
data/raw/fred_real_median_household_income.csv
data/raw/fred_real_disposable_personal_income_per_capita.csv
```

and this import contract:

```text
year
value
```

- [ ] **Step 6: Update methodology with MVP caveat language**

Modify `docs/methodology.md` so the CBO proxy section includes this paragraph:

```markdown
For this MVP, the bundled processed CBO proxy is an executable starter series. It is useful for building and testing the workflow, but it should not be treated as publication-ready until each value is checked against the official CBO supplemental workbook.
```

Ensure the limitations list still explicitly mentions:

```text
household composition
federal taxes versus state/local taxes
transfers
noncash benefits
realized capital gains
health-benefit valuation
```

- [ ] **Step 7: Run notebook/documentation tests**

Run:

```bash
python -m pytest tests/test_notebook.py -q
```

Expected: PASS.

- [ ] **Step 8: Run full test suite**

Run:

```bash
python -m pytest -q
```

Expected: PASS.

- [ ] **Step 9: Commit Task 4**

Run:

```bash
git add README.md docs/data_sources.md docs/methodology.md notebooks/01_cbo_proxy_starter.ipynb tests/test_notebook.py
git commit -m "docs: add MVP usage notes and starter notebook"
```

Expected: commit succeeds.

---

### Task 5: Final Verification And Repo State Review

**Files:**
- Read: all files changed in Tasks 1-4.
- Modify only if verification exposes a concrete defect.

**Interfaces:**
- Consumes all modules, docs, tests, and starter data from previous tasks.
- Produces a verified working MVP scaffold.

- [ ] **Step 1: Run all tests**

Run:

```bash
python -m pytest -q
```

Expected: PASS.

- [ ] **Step 2: Run the plotting script**

Run:

```bash
python scripts/plot_cbo_proxy.py
```

Expected: command prints a CBO proxy summary and saves:

```text
outputs/charts/cbo_proxy_median_adjusted_income.png
```

- [ ] **Step 3: Inspect the generated chart file**

Run:

```bash
test -s outputs/charts/cbo_proxy_median_adjusted_income.png
```

Expected: exit code 0.

- [ ] **Step 4: Run formatting/lint smoke check**

Run:

```bash
python -m ruff check .
```

Expected: PASS.

- [ ] **Step 5: Review git status**

Run:

```bash
git status --short
```

Expected: only intentionally untracked generated outputs are present, or the working tree is clean.

- [ ] **Step 6: Final commit for verification fixes only**

If Steps 1-5 required code or docs fixes, run:

```bash
git add <fixed-files>
git commit -m "chore: verify economics MVP scaffold"
```

Expected: commit succeeds if fixes were needed; skip this step if no fixes were needed.
