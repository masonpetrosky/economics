# CPS/IPUMS Phase 1 Design

## Goal

Build a fixture-backed CPS/IPUMS microdata pipeline that proves the shape of
the final custom estimator before a real IPUMS extract is required.

The phase-1 output is a first custom annual series for median adult-equivalent
disposable resources. Until a real CPS ASEC/IPUMS extract is supplied, any
generated output must be labeled as fixture/demo output rather than research
evidence.

## Scope

This phase adds the microdata processing boundary and estimator contract. It
does not automate IPUMS downloads, finalize a tax model, or claim that the
fixture output is publication-ready.

The implementation should:

- document the expected manual extract file and required columns,
- validate CPS/IPUMS-shaped input data,
- build row-level disposable-resource values from named components,
- apply a small set of sensitivity toggles,
- compute person-weighted annual medians,
- write a processed annual CSV that future charts and tables can consume.

## Source Contract

External downloads remain manual. The future real extract should live at:

```text
data/raw/ipums_cps_asec_extract.csv
```

Phase 1 should not require that real file. Tests should use tiny fixture data
with the same expected schema.

The extract contract should include these conceptual columns:

- `year`: income reference year for the resources being measured. If a future
  real IPUMS extract supplies survey year instead, the real-extract mapping
  layer must normalize it before the estimator runs.
- `serial`: household or household-like identifier.
- `pernum`: person identifier within the household.
- `age`: person age for adult-only sensitivity variants.
- `asecwt`: person weight.
- `household_size`: number of people sharing the resource unit.
- money-income components.
- realized capital-gain components.
- noncash-transfer or benefit components.
- health-insurance value components.
- federal income tax components.
- payroll tax components.
- state and local income tax components, when available.

The first implementation may use project-friendly normalized column names in
fixtures and documentation. A later real-extract step can add an IPUMS variable
mapping layer if the downloaded names differ.

The normalized input should be one row per person. Household or resource-unit
resource values may be repeated across all people in the same unit; the
estimator should not sum repeated household values across person rows before
computing the person-weighted median.

## Architecture

Add a focused `economics.cps` module that composes with the existing package
boundaries:

- `economics.resources` keeps disposable-resource component arithmetic.
- `economics.equivalence` keeps square-root household adjustment.
- `economics.series` keeps weighted medians.
- `economics.cps` owns CPS/IPUMS column validation, resource construction,
  sensitivity handling, annual aggregation, and processed-output metadata.

Keep `economics.metrics` as a compatibility facade only. Export new CPS helpers
from `economics.__init__` if that matches the existing public API pattern.

## Processing Rules

For each person row:

1. Validate that required columns are present.
2. Drop rows with missing or nonpositive person weights.
3. Drop rows with missing or nonpositive household sizes.
4. Build comprehensive disposable resources from the configured components.
5. Apply sensitivity toggles:
   - include versus exclude realized capital gains,
   - include versus exclude health-insurance value,
   - all persons versus adults only.
6. Equivalize resources with the square-root household-size scale.
7. Compute the person-weighted median by year.
8. Return or write a processed annual series.

The processed output should use stable, chart-friendly columns:

```text
year
value
series
source
variant
include_capital_gains
include_health_insurance
population
notes
```

## Command-Line Workflow

Add a CLI script in the implementation phase:

```bash
python scripts/build_cps_ipums_demo.py
```

The script should read a documented input path, default to the future raw
extract location, and write to a processed path such as:

```text
data/processed/cps_ipums_median_adult_equivalent_resources.csv
```

If the real raw file is absent, the script should fail with a clear message
explaining the expected manual file rather than silently falling back to test
fixtures.

## Error Handling

Input validation should raise `ValueError` with the missing column names when a
file does not match the contract. Invalid weights and household sizes should be
handled explicitly so the annual median cannot be distorted by unusable rows.

If no positive-weight observations remain for a requested year or variant, the
estimator should raise a clear error instead of emitting a misleading blank or
zero value.

## Testing

Add focused pytest coverage for:

- required-column validation,
- disposable-resource construction from fixture rows,
- square-root equivalence on CPS-shaped data,
- person-weighted annual medians by year,
- inclusion and exclusion of realized capital gains,
- inclusion and exclusion of health-insurance value,
- all-persons versus adult-only filtering,
- CLI output writing from a tiny fixture file.

The first validation commands should be:

```bash
FF_TMPDIR=/tmp TMPDIR=/tmp TMP=/tmp TEMP=/tmp python -m pytest tests/test_cps_ipums.py -q
FF_TMPDIR=/tmp TMPDIR=/tmp TMP=/tmp TEMP=/tmp python -m pytest -q
python -m ruff check .
```

The explicit temp variables avoid the known WSL/Windows temp-file capture issue
seen in this project environment.

## Documentation

Update `README.md`, `docs/data_sources.md`, and `docs/methodology.md` during
implementation to explain:

- the expected manual IPUMS extract path,
- the normalized fixture schema,
- which output is demo or fixture-backed,
- which output can be treated as real research evidence,
- how the CPS/IPUMS estimate differs from the CBO and FRED public proxies.

## Non-Goals

This phase will not:

- download IPUMS data automatically,
- require IPUMS credentials,
- build a full tax simulation model,
- finalize health-benefit valuation,
- support every planned sensitivity toggle,
- claim fixture-backed output is publication-ready.
