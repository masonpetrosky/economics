# Economics

A transparent data project measuring how the typical American's real disposable resources have changed over time, adjusting for taxes, transfers, inflation, household size, and income composition.

## Project question

Headline labor-market statistics can miss the question people usually care about:

> Can the typical person buy more, less, or the same amount over time?

This repo starts with a practical proxy and builds toward a stronger microdata-based measure.

## Headline target metric

The long-run target is:

**Median adult-equivalent comprehensive disposable resources**

A working definition:

```text
resources =
    cash income
  + realized capital gains
  + noncash benefits
  + employer / public health insurance value
  - personal taxes

adult_equivalent_resources = resources / sqrt(household_size)
```

The project then assigns household-level resources to people, uses person weights, and takes the median person. This avoids relying on raw household income, which can be distorted by long-run changes in marriage rates, household size, and living arrangements.

## MVP approach

The first version uses a close public proxy:

**CBO median adjusted household income after transfers and federal taxes**

This is not perfect, but it is useful because CBO already adjusts household income for household size and includes a broad set of income, transfer, tax, and benefit concepts.

The seed data in this repo starts with CBO's 1979-2022 proxy series discussed in `docs/methodology.md`.

## Why not just use median household income?

Raw household income is useful but incomplete for this project because households are not a stable unit over time. Marriage rates, household size, living-alone rates, and multi-earner household composition all change.

Better options:

1. **Real median personal income**: clean individual series, but before taxes and missing noncash benefits.
2. **Real disposable personal income per capita**: broad after-tax purchasing-power average, but it is a mean, not a median.
3. **Median equivalized after-tax/transfer resources**: closest to the intended living-standard concept.
4. **CBO proxy**: strong first public benchmark.
5. **CPS ASEC/IPUMS microdata build**: eventual custom version.

## Suggested repo workflow

1. Reproduce the CBO proxy chart.
2. Add FRED/Census comparison series.
3. Build a CPS ASEC/IPUMS data pipeline.
4. Add sensitivity toggles:
   - with and without realized capital gains,
   - with and without health benefits,
   - CPI versus PCE deflator,
   - all persons versus adults only,
   - square-root equivalence scale versus per-capita scale.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate  # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install pandas matplotlib
python scripts/plot_cbo_proxy.py
```

The chart will be saved to:

```text
outputs/charts/cbo_proxy_median_adjusted_income.png
```

## Current starter files

```text
docs/methodology.md
docs/data_sources.md
src/economics/metrics.py
scripts/plot_cbo_proxy.py
data/processed/cbo_proxy_median_adjusted_income_after_tax_transfer.csv
```

## Status

This is a starter scaffold, not a final research product. The CBO proxy values should be verified against the official CBO supplemental workbook before publication.
