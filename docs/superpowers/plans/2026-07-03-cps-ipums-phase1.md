# CPS/IPUMS Phase 1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a fixture-backed CPS/IPUMS microdata pipeline that validates normalized person-level input, computes person-weighted annual medians, and documents the manual extract contract.

**Architecture:** Add a focused `economics.cps` module for CPS/IPUMS-specific validation, row-level resource construction, sensitivity variants, and annual aggregation. Reuse existing package helpers for missing-column errors, square-root equivalence, and weighted medians. Add one CLI script that reads a manual normalized extract and writes a processed annual CSV.

**Tech Stack:** Python 3.12, pandas, pathlib, argparse, pytest, ruff.

## Global Constraints

- External downloads remain manual.
- The future real extract path is `data/raw/ipums_cps_asec_extract.csv`.
- Phase 1 must not require a real CPS ASEC/IPUMS extract for tests.
- Normalized CPS/IPUMS input is one row per person.
- `year` means income reference year for the resources being measured.
- Household or resource-unit values may be repeated across person rows and must not be summed before the person-weighted median.
- No automatic IPUMS downloads.
- No IPUMS credentials.
- No full tax simulation model.
- No finalized health-benefit valuation.
- Fixture-backed output must be labeled as demo output rather than research evidence.
- Use `FF_TMPDIR=/tmp TMPDIR=/tmp TMP=/tmp TEMP=/tmp` with pytest in this WSL environment.

---

## File Structure

- Create `src/economics/cps.py`: normalized CPS/IPUMS schema, `CpsVariant`, resource construction, annual median estimation, and output metadata.
- Modify `src/economics/loaders.py`: add the normalized CPS/IPUMS required-column tuple and raw source-file registry entry.
- Modify `src/economics/__init__.py`: export the new CPS helpers.
- Create `tests/test_cps_ipums.py`: fixture-backed unit and CLI tests for the CPS/IPUMS path.
- Create `scripts/build_cps_ipums_demo.py`: CLI for manual normalized extract to processed CSV.
- Modify `README.md`: add the manual CPS/IPUMS workflow and status caveat.
- Modify `docs/data_sources.md`: add the normalized CPS/IPUMS extract contract.
- Modify `docs/methodology.md`: explain the custom microdata estimator boundary and demo-output caveat.

---

### Task 1: Normalized CPS/IPUMS Estimator

**Files:**
- Create: `tests/test_cps_ipums.py`
- Create: `src/economics/cps.py`
- Modify: `src/economics/loaders.py`
- Modify: `src/economics/__init__.py`

**Interfaces:**
- Consumes: `economics.loaders.validate_required_columns(df, required_columns, source_label)`, `economics.equivalence.equivalize_resources(resources, household_size)`, and `economics.series.weighted_median(values, weights)`.
- Produces:
  - `CPS_IPUMS_REQUIRED_COLUMNS: tuple[str, ...]`
  - `CpsVariant(include_capital_gains: bool = True, include_health_insurance: bool = True, population: str = "all", adult_age_min: int = 18)`
  - `validate_cps_columns(df: pd.DataFrame, source_label: str = "CPS/IPUMS input") -> None`
  - `build_cps_person_resources(df: pd.DataFrame, variant: CpsVariant = CpsVariant()) -> pd.DataFrame`
  - `estimate_cps_annual_medians(df: pd.DataFrame, variant: CpsVariant = CpsVariant(), series: str = "Median adult-equivalent disposable resources", source: str = "CPS ASEC/IPUMS normalized extract", notes: str = "Fixture/demo output until built from a real IPUMS extract.") -> pd.DataFrame`

- [ ] **Step 1: Write failing estimator tests**

Create `tests/test_cps_ipums.py` with:

```python
from __future__ import annotations

import pandas as pd
import pytest

from economics.cps import (
    CpsVariant,
    build_cps_person_resources,
    estimate_cps_annual_medians,
    validate_cps_columns,
)


def cps_fixture() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "year": 2020,
                "serial": 1,
                "pernum": 1,
                "age": 10,
                "asecwt": 5,
                "household_size": 1,
                "money_income": 10_000,
                "realized_capital_gains": 1_000,
                "noncash_benefits": 0,
                "health_insurance_value": 0,
                "federal_income_taxes": 0,
                "payroll_taxes": 0,
                "state_local_income_taxes": 0,
            },
            {
                "year": 2020,
                "serial": 2,
                "pernum": 1,
                "age": 30,
                "asecwt": 1,
                "household_size": 1,
                "money_income": 50_000,
                "realized_capital_gains": 10_000,
                "noncash_benefits": 0,
                "health_insurance_value": 5_000,
                "federal_income_taxes": 3_000,
                "payroll_taxes": 1_500,
                "state_local_income_taxes": 500,
            },
            {
                "year": 2021,
                "serial": 3,
                "pernum": 1,
                "age": 40,
                "asecwt": 1,
                "household_size": 4,
                "money_income": 80_000,
                "realized_capital_gains": 0,
                "noncash_benefits": 0,
                "health_insurance_value": 0,
                "federal_income_taxes": 0,
                "payroll_taxes": 0,
                "state_local_income_taxes": 0,
            },
        ]
    )


def test_validate_cps_columns_reports_missing_columns() -> None:
    df = cps_fixture().drop(columns=["age"])

    with pytest.raises(ValueError, match="CPS fixture missing required columns: \\['age'\\]"):
        validate_cps_columns(df, source_label="CPS fixture")


def test_build_cps_person_resources_applies_components_and_equivalence() -> None:
    rows = build_cps_person_resources(cps_fixture(), CpsVariant(population="adults"))

    assert rows[["year", "pernum", "comprehensive_resources", "equivalized_resources"]].to_dict(
        "records"
    ) == [
        {
            "year": 2020,
            "pernum": 1,
            "comprehensive_resources": 60_000.0,
            "equivalized_resources": 60_000.0,
        },
        {
            "year": 2021,
            "pernum": 1,
            "comprehensive_resources": 80_000.0,
            "equivalized_resources": 40_000.0,
        },
    ]


def test_estimate_cps_annual_medians_uses_person_weights_by_year() -> None:
    medians = estimate_cps_annual_medians(cps_fixture())

    assert medians[["year", "value", "variant", "population"]].to_dict("records") == [
        {
            "year": 2020,
            "value": 11_000.0,
            "variant": "all_with_capital_gains_with_health_insurance",
            "population": "all",
        },
        {
            "year": 2021,
            "value": 40_000.0,
            "variant": "all_with_capital_gains_with_health_insurance",
            "population": "all",
        },
    ]
    assert medians["series"].unique().tolist() == [
        "Median adult-equivalent disposable resources"
    ]
    assert medians["source"].unique().tolist() == ["CPS ASEC/IPUMS normalized extract"]


def test_estimate_cps_annual_medians_supports_adult_population_filter() -> None:
    medians = estimate_cps_annual_medians(cps_fixture(), CpsVariant(population="adults"))

    assert medians[["year", "value", "population"]].to_dict("records") == [
        {"year": 2020, "value": 60_000.0, "population": "adults"},
        {"year": 2021, "value": 40_000.0, "population": "adults"},
    ]


def test_estimate_cps_annual_medians_supports_capital_gains_and_health_toggles() -> None:
    variant = CpsVariant(
        include_capital_gains=False,
        include_health_insurance=False,
        population="adults",
    )

    medians = estimate_cps_annual_medians(cps_fixture(), variant)

    assert medians[["year", "value", "variant"]].to_dict("records") == [
        {
            "year": 2020,
            "value": 45_000.0,
            "variant": "adults_without_capital_gains_without_health_insurance",
        },
        {
            "year": 2021,
            "value": 40_000.0,
            "variant": "adults_without_capital_gains_without_health_insurance",
        },
    ]


def test_estimate_cps_annual_medians_drops_invalid_weights_and_household_sizes() -> None:
    df = pd.concat(
        [
            cps_fixture(),
            pd.DataFrame(
                [
                    {
                        "year": 2020,
                        "serial": 9,
                        "pernum": 1,
                        "age": 60,
                        "asecwt": 0,
                        "household_size": 1,
                        "money_income": 1,
                        "realized_capital_gains": 0,
                        "noncash_benefits": 0,
                        "health_insurance_value": 0,
                        "federal_income_taxes": 0,
                        "payroll_taxes": 0,
                        "state_local_income_taxes": 0,
                    },
                    {
                        "year": 2020,
                        "serial": 10,
                        "pernum": 1,
                        "age": 60,
                        "asecwt": 100,
                        "household_size": 0,
                        "money_income": 1,
                        "realized_capital_gains": 0,
                        "noncash_benefits": 0,
                        "health_insurance_value": 0,
                        "federal_income_taxes": 0,
                        "payroll_taxes": 0,
                        "state_local_income_taxes": 0,
                    },
                ]
            ),
        ],
        ignore_index=True,
    )

    medians = estimate_cps_annual_medians(df)

    assert medians.loc[medians["year"] == 2020, "value"].iloc[0] == 11_000.0


def test_estimate_cps_annual_medians_rejects_empty_filtered_data() -> None:
    df = cps_fixture()
    df["asecwt"] = 0

    with pytest.raises(
        ValueError,
        match="No CPS observations remain after filtering invalid weights and household sizes",
    ):
        estimate_cps_annual_medians(df)


def test_cps_variant_rejects_unknown_population() -> None:
    with pytest.raises(ValueError, match="population must be one of: all, adults"):
        CpsVariant(population="children")
```

- [ ] **Step 2: Run the failing tests**

Run:

```bash
FF_TMPDIR=/tmp TMPDIR=/tmp TMP=/tmp TEMP=/tmp ./.venv/bin/python -m pytest tests/test_cps_ipums.py -q
```

Expected: FAIL during import with `ModuleNotFoundError: No module named 'economics.cps'`.

- [ ] **Step 3: Add the normalized CPS/IPUMS source contract**

Modify `src/economics/loaders.py` by adding this constant after `CBO_PROXY_VALUE_COL`:

```python
CPS_IPUMS_REQUIRED_COLUMNS = (
    "year",
    "serial",
    "pernum",
    "age",
    "asecwt",
    "household_size",
    "money_income",
    "realized_capital_gains",
    "noncash_benefits",
    "health_insurance_value",
    "federal_income_taxes",
    "payroll_taxes",
    "state_local_income_taxes",
)
```

Add this entry to `RAW_SOURCE_FILE_SPECS`:

```python
    "ipums_cps_asec_extract": SourceFileSpec(
        file_name="ipums_cps_asec_extract.csv",
        required_columns=CPS_IPUMS_REQUIRED_COLUMNS,
        description=(
            "Normalized CPS ASEC/IPUMS person-level extract for custom "
            "adult-equivalent disposable-resource estimates."
        ),
    ),
```

- [ ] **Step 4: Implement the estimator module**

Create `src/economics/cps.py`:

```python
"""CPS ASEC/IPUMS microdata helpers."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

import pandas as pd

from economics.equivalence import equivalize_resources
from economics.loaders import CPS_IPUMS_REQUIRED_COLUMNS, validate_required_columns
from economics.series import weighted_median

DEFAULT_CPS_SERIES = "Median adult-equivalent disposable resources"
DEFAULT_CPS_SOURCE = "CPS ASEC/IPUMS normalized extract"
DEFAULT_CPS_NOTES = "Fixture/demo output until built from a real IPUMS extract."
VALID_POPULATIONS = ("all", "adults")
RESOURCE_COMPONENT_COLUMNS = (
    "money_income",
    "realized_capital_gains",
    "noncash_benefits",
    "health_insurance_value",
    "federal_income_taxes",
    "payroll_taxes",
    "state_local_income_taxes",
)
NUMERIC_COLUMNS = (
    "year",
    "age",
    "asecwt",
    "household_size",
    *RESOURCE_COMPONENT_COLUMNS,
)


@dataclass(frozen=True)
class CpsVariant:
    """Sensitivity switches for normalized CPS/IPUMS estimation."""

    include_capital_gains: bool = True
    include_health_insurance: bool = True
    population: str = "all"
    adult_age_min: int = 18

    def __post_init__(self) -> None:
        """Validate variant values at construction time."""

        if self.population not in VALID_POPULATIONS:
            raise ValueError("population must be one of: all, adults")
        if self.adult_age_min <= 0:
            raise ValueError("adult_age_min must be positive")

    @property
    def label(self) -> str:
        """Return a stable variant label for processed output."""

        gains = "with_capital_gains" if self.include_capital_gains else "without_capital_gains"
        health = (
            "with_health_insurance"
            if self.include_health_insurance
            else "without_health_insurance"
        )
        return f"{self.population}_{gains}_{health}"


def validate_cps_columns(
    df: pd.DataFrame,
    source_label: str = "CPS/IPUMS input",
    required_columns: Iterable[str] = CPS_IPUMS_REQUIRED_COLUMNS,
) -> None:
    """Raise a clear error if normalized CPS/IPUMS input lacks required columns."""

    validate_required_columns(df, required_columns, source_label)


def build_cps_person_resources(
    df: pd.DataFrame,
    variant: CpsVariant = CpsVariant(),
) -> pd.DataFrame:
    """Return person rows with comprehensive and equivalized resources."""

    validate_cps_columns(df)
    work = df.copy()
    for column in NUMERIC_COLUMNS:
        work[column] = pd.to_numeric(work[column], errors="coerce")

    work = work.dropna(subset=NUMERIC_COLUMNS)
    work = work[(work["asecwt"] > 0) & (work["household_size"] > 0)]
    if work.empty:
        raise ValueError(
            "No CPS observations remain after filtering invalid weights and household sizes"
        )

    if variant.population == "adults":
        work = work[work["age"] >= variant.adult_age_min]
        if work.empty:
            raise ValueError("No CPS observations remain after applying population filter: adults")

    capital_gains = (
        work["realized_capital_gains"] if variant.include_capital_gains else 0.0
    )
    health_insurance = (
        work["health_insurance_value"] if variant.include_health_insurance else 0.0
    )
    taxes = (
        work["federal_income_taxes"]
        + work["payroll_taxes"]
        + work["state_local_income_taxes"]
    )

    out = work.copy()
    out["year"] = out["year"].astype(int)
    out["comprehensive_resources"] = (
        work["money_income"] + capital_gains + work["noncash_benefits"] + health_insurance - taxes
    )
    out["equivalized_resources"] = [
        equivalize_resources(resources, household_size)
        for resources, household_size in zip(
            out["comprehensive_resources"],
            out["household_size"],
            strict=True,
        )
    ]
    return out.reset_index(drop=True)


def estimate_cps_annual_medians(
    df: pd.DataFrame,
    variant: CpsVariant = CpsVariant(),
    series: str = DEFAULT_CPS_SERIES,
    source: str = DEFAULT_CPS_SOURCE,
    notes: str = DEFAULT_CPS_NOTES,
) -> pd.DataFrame:
    """Estimate person-weighted annual medians from normalized CPS/IPUMS rows."""

    person_rows = build_cps_person_resources(df, variant)
    rows: list[dict[str, float | int | str | bool]] = []
    for year, year_rows in person_rows.groupby("year", sort=True):
        rows.append(
            {
                "year": int(year),
                "value": weighted_median(
                    year_rows["equivalized_resources"],
                    year_rows["asecwt"],
                ),
                "series": series,
                "source": source,
                "variant": variant.label,
                "include_capital_gains": variant.include_capital_gains,
                "include_health_insurance": variant.include_health_insurance,
                "population": variant.population,
                "notes": notes,
            }
        )

    if not rows:
        raise ValueError("No annual CPS medians could be estimated")

    return pd.DataFrame(rows).sort_values("year").reset_index(drop=True)
```

- [ ] **Step 5: Export the CPS helpers**

Modify `src/economics/__init__.py` by adding imports:

```python
from economics.cps import (
    CpsVariant,
    build_cps_person_resources,
    estimate_cps_annual_medians,
)
```

Add these strings to `__all__`:

```python
    "CpsVariant",
    "build_cps_person_resources",
    "estimate_cps_annual_medians",
```

- [ ] **Step 6: Run the focused tests**

Run:

```bash
FF_TMPDIR=/tmp TMPDIR=/tmp TMP=/tmp TEMP=/tmp ./.venv/bin/python -m pytest tests/test_cps_ipums.py -q
```

Expected: PASS with 8 tests passing.

- [ ] **Step 7: Run existing core tests that import package exports**

Run:

```bash
FF_TMPDIR=/tmp TMPDIR=/tmp TMP=/tmp TEMP=/tmp ./.venv/bin/python -m pytest tests/test_core_metrics.py tests/test_loaders.py -q
```

Expected: PASS.

- [ ] **Step 8: Commit Task 1**

Run:

```bash
git add src/economics/cps.py src/economics/loaders.py src/economics/__init__.py tests/test_cps_ipums.py
git commit -m "feat: add CPS IPUMS estimator"
```

---

### Task 2: CPS/IPUMS Demo Build CLI

**Files:**
- Modify: `tests/test_cps_ipums.py`
- Create: `scripts/build_cps_ipums_demo.py`

**Interfaces:**
- Consumes: `CpsVariant` and `estimate_cps_annual_medians` from Task 1.
- Produces: `python scripts/build_cps_ipums_demo.py --raw-csv <path> --out <path>` command that writes a processed CSV with `year`, `value`, `series`, `source`, `variant`, `include_capital_gains`, `include_health_insurance`, `population`, and `notes`.

- [ ] **Step 1: Add failing CLI tests**

Change the import block at the top of `tests/test_cps_ipums.py` to:

```python
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest

from economics.cps import (
    CpsVariant,
    build_cps_person_resources,
    estimate_cps_annual_medians,
    validate_cps_columns,
)
from economics.paths import repo_root
```

Then append these helpers and tests to `tests/test_cps_ipums.py`:

```python


def write_cps_fixture_csv(path: Path) -> None:
    cps_fixture().to_csv(path, index=False)


def test_build_cps_ipums_demo_script_writes_processed_csv(tmp_path: Path) -> None:
    raw_csv = tmp_path / "ipums_cps_asec_extract.csv"
    out_csv = tmp_path / "processed.csv"
    write_cps_fixture_csv(raw_csv)

    result = subprocess.run(
        [
            sys.executable,
            str(repo_root() / "scripts" / "build_cps_ipums_demo.py"),
            "--raw-csv",
            str(raw_csv),
            "--out",
            str(out_csv),
        ],
        cwd=repo_root(),
        check=True,
        capture_output=True,
        text=True,
    )

    output = pd.read_csv(out_csv)

    assert "Wrote 2 CPS/IPUMS median rows" in result.stdout
    assert list(output.columns) == [
        "year",
        "value",
        "series",
        "source",
        "variant",
        "include_capital_gains",
        "include_health_insurance",
        "population",
        "notes",
    ]
    assert output["notes"].unique().tolist() == [
        "Fixture/demo output until built from a real IPUMS extract."
    ]


def test_build_cps_ipums_demo_script_reports_missing_raw_file(tmp_path: Path) -> None:
    missing_raw = tmp_path / "missing.csv"
    out_csv = tmp_path / "processed.csv"

    result = subprocess.run(
        [
            sys.executable,
            str(repo_root() / "scripts" / "build_cps_ipums_demo.py"),
            "--raw-csv",
            str(missing_raw),
            "--out",
            str(out_csv),
        ],
        cwd=repo_root(),
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert f"Expected CPS/IPUMS input file not found: {missing_raw}" in result.stderr
    assert not out_csv.exists()
```

- [ ] **Step 2: Run the failing CLI tests**

Run:

```bash
FF_TMPDIR=/tmp TMPDIR=/tmp TMP=/tmp TEMP=/tmp ./.venv/bin/python -m pytest tests/test_cps_ipums.py::test_build_cps_ipums_demo_script_writes_processed_csv tests/test_cps_ipums.py::test_build_cps_ipums_demo_script_reports_missing_raw_file -q
```

Expected: FAIL because `scripts/build_cps_ipums_demo.py` does not exist.

- [ ] **Step 3: Implement the CLI script**

Create `scripts/build_cps_ipums_demo.py`:

```python
"""Build a CPS/IPUMS median resources CSV from a normalized manual extract.

Run from the repo root:

    python scripts/build_cps_ipums_demo.py
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = REPO_ROOT / "src"
DEFAULT_RAW_CSV = REPO_ROOT / "data" / "raw" / "ipums_cps_asec_extract.csv"
DEFAULT_OUT = (
    REPO_ROOT
    / "data"
    / "processed"
    / "cps_ipums_median_adult_equivalent_resources.csv"
)


def _add_src_to_path() -> None:
    """Allow direct script execution without requiring package installation."""

    if str(SRC_PATH) not in sys.path:
        sys.path.insert(0, str(SRC_PATH))


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""

    parser = argparse.ArgumentParser(
        description="Build CPS/IPUMS median adult-equivalent resources from normalized input."
    )
    parser.add_argument(
        "--raw-csv",
        type=Path,
        default=DEFAULT_RAW_CSV,
        help=f"Normalized CPS/IPUMS input CSV. Default: {DEFAULT_RAW_CSV}",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=DEFAULT_OUT,
        help=f"Processed CSV output path. Default: {DEFAULT_OUT}",
    )
    parser.add_argument(
        "--population",
        choices=["all", "adults"],
        default="all",
        help="Population filter for the median estimate. Default: all",
    )
    parser.add_argument(
        "--exclude-capital-gains",
        action="store_true",
        help="Exclude realized capital gains from resources.",
    )
    parser.add_argument(
        "--exclude-health-insurance",
        action="store_true",
        help="Exclude health insurance value from resources.",
    )
    return parser.parse_args()


def main() -> int:
    """Run the CPS/IPUMS build."""

    _add_src_to_path()
    from economics.cps import CpsVariant, estimate_cps_annual_medians

    args = parse_args()
    if not args.raw_csv.exists():
        print(f"Expected CPS/IPUMS input file not found: {args.raw_csv}", file=sys.stderr)
        return 1

    raw = pd.read_csv(args.raw_csv)
    variant = CpsVariant(
        include_capital_gains=not args.exclude_capital_gains,
        include_health_insurance=not args.exclude_health_insurance,
        population=args.population,
    )
    output = estimate_cps_annual_medians(raw, variant)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    output.to_csv(args.out, index=False)
    print(f"Wrote {len(output)} CPS/IPUMS median rows to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run the CLI tests**

Run:

```bash
FF_TMPDIR=/tmp TMPDIR=/tmp TMP=/tmp TEMP=/tmp ./.venv/bin/python -m pytest tests/test_cps_ipums.py::test_build_cps_ipums_demo_script_writes_processed_csv tests/test_cps_ipums.py::test_build_cps_ipums_demo_script_reports_missing_raw_file -q
```

Expected: PASS.

- [ ] **Step 5: Run all CPS/IPUMS tests**

Run:

```bash
FF_TMPDIR=/tmp TMPDIR=/tmp TMP=/tmp TEMP=/tmp ./.venv/bin/python -m pytest tests/test_cps_ipums.py -q
```

Expected: PASS with 10 tests passing.

- [ ] **Step 6: Commit Task 2**

Run:

```bash
git add scripts/build_cps_ipums_demo.py tests/test_cps_ipums.py
git commit -m "feat: add CPS IPUMS build script"
```

---

### Task 3: Documentation And Source Notes

**Files:**
- Modify: `README.md`
- Modify: `docs/data_sources.md`
- Modify: `docs/methodology.md`

**Interfaces:**
- Consumes: CLI command from Task 2 and normalized schema from Task 1.
- Produces: user-facing instructions for the manual normalized CPS/IPUMS extract and clear fixture/demo caveats.

- [ ] **Step 1: Update README workflow text**

Modify `README.md` by adding `data/raw/ipums_cps_asec_extract.csv` to the manual source-file expectations block:

```text
data/raw/ipums_cps_asec_extract.csv
```

Add this section after the public proxy summary table section:

````markdown
## Build the CPS/IPUMS demo microdata estimate

Phase 1 of the custom microdata path expects a manually prepared normalized
CPS ASEC/IPUMS extract at:

```text
data/raw/ipums_cps_asec_extract.csv
```

The normalized extract is one row per person and uses income-reference `year`,
person weight `asecwt`, `household_size`, and named resource and tax component
columns documented in `docs/data_sources.md`.

Run:

```bash
python scripts/build_cps_ipums_demo.py
```

The script writes:

```text
data/processed/cps_ipums_median_adult_equivalent_resources.csv
```

Until the input is built from a real CPS ASEC/IPUMS extract, this workflow is a
schema and estimator demonstration rather than research evidence.
````

- [ ] **Step 2: Update data source notes**

Modify the `CPS ASEC / IPUMS CPS` section in `docs/data_sources.md` so it includes:

````markdown
Expected normalized manual file:

```text
data/raw/ipums_cps_asec_extract.csv
```

Normalized phase-1 columns:

```text
year
serial
pernum
age
asecwt
household_size
money_income
realized_capital_gains
noncash_benefits
health_insurance_value
federal_income_taxes
payroll_taxes
state_local_income_taxes
```

`year` is the income reference year. The normalized file is one row per person.
Household or resource-unit values may be repeated across people in the same
unit so the estimator can compute a person-weighted median without summing
household values across person rows.
````

- [ ] **Step 3: Update methodology notes**

Modify `docs/methodology.md` near the preferred target metric or planned sensitivity section with:

```markdown
## CPS/IPUMS phase-1 estimator boundary

The first custom microdata implementation uses a normalized CPS ASEC/IPUMS-shaped
person file to prove the estimator contract before depending on a real extract.
It validates one row per person, builds disposable-resource components, applies
the square-root household-size adjustment, and calculates person-weighted annual
medians.

The phase-1 toggles cover realized capital gains, health-insurance value, and
all-persons versus adult-only populations. Output built from fixtures or
handmade demo files is not research evidence; publication-quality interpretation
requires a real CPS ASEC/IPUMS extract and a reviewed variable mapping.
```

- [ ] **Step 4: Verify docs mention the contract and caveat**

Run:

```bash
rg -n "ipums_cps_asec_extract.csv|one row per person|Fixture/demo|not research evidence|CPS/IPUMS phase-1" README.md docs/data_sources.md docs/methodology.md
```

Expected: matches in all three documentation files.

- [ ] **Step 5: Run relevant tests and lint**

Run:

```bash
FF_TMPDIR=/tmp TMPDIR=/tmp TMP=/tmp TEMP=/tmp ./.venv/bin/python -m pytest tests/test_cps_ipums.py tests/test_loaders.py -q
./.venv/bin/python -m ruff check .
```

Expected: pytest PASS and ruff `All checks passed!`.

- [ ] **Step 6: Commit Task 3**

Run:

```bash
git add README.md docs/data_sources.md docs/methodology.md
git commit -m "docs: document CPS IPUMS extract contract"
```

---

### Task 4: Full Validation

**Files:**
- Verify: all files changed by Tasks 1 through 3.

**Interfaces:**
- Consumes: package module, CLI, tests, and docs from Tasks 1 through 3.
- Produces: verified local branch ready for review, push, or PR.

- [ ] **Step 1: Run the full test suite**

Run:

```bash
FF_TMPDIR=/tmp TMPDIR=/tmp TMP=/tmp TEMP=/tmp ./.venv/bin/python -m pytest -q
```

Expected: PASS with all tests passing.

- [ ] **Step 2: Run lint**

Run:

```bash
./.venv/bin/python -m ruff check .
```

Expected: `All checks passed!`

- [ ] **Step 3: Smoke-test the CPS/IPUMS CLI with a temporary normalized fixture**

Run:

```bash
tmpdir="$(mktemp -d)"
cat > "$tmpdir/ipums_cps_asec_extract.csv" <<'CSV'
year,serial,pernum,age,asecwt,household_size,money_income,realized_capital_gains,noncash_benefits,health_insurance_value,federal_income_taxes,payroll_taxes,state_local_income_taxes
2020,1,1,30,1,1,50000,10000,0,5000,3000,1500,500
2021,2,1,40,1,4,80000,0,0,0,0,0,0
CSV
./.venv/bin/python scripts/build_cps_ipums_demo.py \
  --raw-csv "$tmpdir/ipums_cps_asec_extract.csv" \
  --out "$tmpdir/cps_ipums_median_adult_equivalent_resources.csv"
cat "$tmpdir/cps_ipums_median_adult_equivalent_resources.csv"
```

Expected output includes:

```text
Wrote 2 CPS/IPUMS median rows
```

Expected CSV rows include `2020,60000.0` and `2021,40000.0`.

- [ ] **Step 4: Check repository whitespace**

Run:

```bash
git diff --check
```

Expected: no output and exit code 0.

- [ ] **Step 5: Review final changed files**

Run:

```bash
git status --short --branch
git log --oneline --decorate -5
```

Expected: branch contains the three implementation commits from Tasks 1 through 3, with no unstaged changes.
