# CPS/IPUMS Real-Dollar QA Design

## Goal

Make the CPS/IPUMS microdata series interpretable as a real purchasing-power
measure before it is compared to CBO and FRED public proxy series.

The current CPS/IPUMS pipeline produces a full 1991-2024 annual series from the
local rectangularized IPUMS extract, but the output values are nominal CPS
dollars. The next phase should preserve that nominal output, add a clearly
labeled real-dollar output, and produce a compact QA comparison against the
project's existing public proxy series.

## Scope

This phase adds the price-index boundary and QA checks needed to decide whether
the CPS/IPUMS trend is directionally plausible. It does not finalize the broader
resource concept.

The implementation should:

- document the manual price-index input contract,
- validate an annual deflator file,
- convert CPS/IPUMS nominal medians to base-year real dollars,
- keep nominal and real CPS outputs distinguishable,
- write an indexed public-proxy QA table and chart,
- update docs so readers do not interpret nominal CPS growth as real growth.

## Current Evidence

The existing CPS/IPUMS output has strong row retention in the preflight summary:
most years keep 99.99% to 100.00% of rows after estimator filtering.

The main blocker is dollar comparability. Over the common 1991-2022 window, the
nominal CPS/IPUMS series currently grows about 168%, while the existing real
public proxies grow roughly 25% to 70%. That gap is expected if the CPS series is
still nominal, and it should be resolved before presentation work.

## Source Contract

External downloads remain manual. Add a documented raw price-index file at:

```text
data/raw/annual_price_index.csv
```

The first implementation should accept a simple project-shaped CSV:

```text
year
price_index
```

Optional metadata columns such as `series_id`, `series`, `source`, and `notes`
may be passed through when present, but the estimator should only require
`year` and `price_index`.

The default base year should be 2024 because the FRED/Census median personal and
household comparison series are already expressed in 2024 C-CPI-U dollars. The
QA comparison should still index all series to a common starting year, because
CBO and FRED use different dollar bases and concepts.

## Architecture

Add a focused price-index helper rather than embedding deflator logic inside the
CPS module:

- `economics.prices` owns annual price-index validation and real-dollar
  conversion.
- `economics.series.real_value` remains the low-level scalar helper.
- `economics.cps` continues to own CPS/IPUMS resource construction and annual
  nominal median estimation.
- `scripts/build_cps_ipums_real.py` writes the real-dollar CPS output after the
  nominal CPS output exists.
- `scripts/build_cps_public_proxy_qa.py` writes the indexed QA table and chart
  from existing processed outputs.

The preferred output path is:

```text
data/processed/cps_ipums_median_adult_equivalent_resources_real.csv
```

Keep the existing nominal output path:

```text
data/processed/cps_ipums_median_adult_equivalent_resources.csv
```

## Processing Rules

For CPS/IPUMS real-dollar conversion:

1. Read the nominal CPS processed CSV.
2. Read and validate the annual price-index CSV.
3. Reject duplicate price-index years.
4. Reject missing or nonpositive price-index values.
5. Require a price-index row for every CPS year being converted.
6. Require the requested base year to exist in the price index.
7. Convert nominal CPS values with:

```text
real_value = nominal_value * base_year_price_index / year_price_index
```

8. Write stable output columns:

```text
year
value
nominal_value
price_index
real_base_year
series
source
variant
include_capital_gains
include_health_insurance
population
notes
```

In the real-dollar output, `value` should mean real dollars in the configured
base year. `nominal_value` preserves the original CPS median for auditability.

## QA Artifacts

Add a compact public-proxy QA output that joins:

- CPS/IPUMS real-dollar median adult-equivalent resources,
- CBO median adjusted household income after transfers and taxes,
- FRED real median personal income,
- FRED real median household income,
- FRED real disposable personal income per capita.

The QA table should use the common overlap window and index each series to 100
in the first shared year. Suggested output:

```text
outputs/tables/cps_public_proxy_qa_summary.csv
```

Suggested chart:

```text
outputs/charts/cps_public_proxy_indexed_comparison.png
```

The QA chart should be treated as a diagnostic, not as the final project chart.
It should make trend differences visible while the methodology still excludes
noncash benefits, health-insurance value, and reviewed resource-unit treatment.

## Error Handling

Price-index validation should raise clear `ValueError` messages for:

- missing required columns,
- duplicate years,
- nonnumeric years or price-index values,
- nonpositive price-index values,
- missing CPS years in the deflator file,
- missing base year in the deflator file.

The CLI should fail with a clear file-not-found message when the manual price
index is absent. It should not silently fall back to an implicit deflator.

## Testing

Add focused pytest coverage for:

- annual price-index validation,
- real-dollar conversion math,
- duplicate-year and missing-year failures,
- nonpositive price-index failures,
- base-year validation,
- CPS real-output schema from a tiny fixture,
- `scripts/build_cps_ipums_real.py` output writing from fixture files,
- indexed QA comparison on small fixture series.

The first validation commands should be:

```bash
FF_TMPDIR=/tmp TMPDIR=/tmp TMP=/tmp TEMP=/tmp ./.venv/bin/python -m pytest tests/test_prices.py tests/test_cps_ipums_real.py -q
FF_TMPDIR=/tmp TMPDIR=/tmp TMP=/tmp TEMP=/tmp ./.venv/bin/python -m pytest -q
./.venv/bin/python -m ruff check .
git diff --check
```

If the manual price-index raw file is present locally, also run the real build
and inspect the generated QA table for the common 1991-2022 span.

## Documentation

Update `README.md`, `docs/data_sources.md`, and `docs/methodology.md` to explain:

- the manual annual price-index file,
- the selected default real-dollar base year,
- the distinction between nominal and real CPS/IPUMS outputs,
- why indexed public-proxy QA is safer than level comparison across concepts,
- that this phase fixes inflation comparability but not the remaining resource
  concept limitations.

## Non-Goals

This phase will not:

- download price-index data automatically,
- choose a permanent publication deflator for every sensitivity,
- finalize noncash benefit or health-insurance valuation,
- solve resource-unit allocation beyond the current household-level starter
  bridge,
- replace the existing CBO/FRED public proxy charts,
- claim the CPS/IPUMS real output is publication-ready.
