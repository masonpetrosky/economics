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
It can be rebuilt from CBO's official Additional Data for Researchers ZIP.

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
data/raw/61911-additional-data-for-researchers.zip
data/raw/fred_real_median_personal_income.csv
data/raw/fred_real_median_household_income.csv
data/raw/fred_real_disposable_personal_income_per_capita.csv
```

For FRED comparison metrics, the builder accepts direct FRED graph CSV exports with
`observation_date,<FRED_SERIES_ID>` columns or project-shaped CSVs with `year,value`
columns.
The CBO proxy builder expects CBO's official researchers ZIP at:

```text
data/raw/61911-additional-data-for-researchers.zip
```

Inside that ZIP, the builder reads:

```text
61911-additional-data-for-researchers/CBO_distribution_household_income_2022_data/households_ranked_by_inc_after_trans_tax_table_04_median_household_income_1979_2022.csv
```

## Starter notebook

Open:

```text
notebooks/01_cbo_proxy_starter.ipynb
```

The notebook loads the bundled CBO proxy, prints a summary table, and plots the proxy metric.
Treat the CBO proxy as the first benchmark, not the final custom measure.

## Rebuild the CBO proxy data

Manually download CBO's `61911-additional-data-for-researchers.zip` file into `data/raw/`, then run:

```bash
python scripts/build_cbo_proxy.py
```

The script writes:

```text
data/processed/cbo_proxy_median_adjusted_income_after_tax_transfer.csv
```

## Rebuild the FRED comparison data

Manually download FRED graph CSV exports into the documented `data/raw/fred_*.csv`
paths, then run:

```bash
python scripts/build_fred_comparisons.py
```

The script writes:

```text
data/processed/fred_real_median_personal_income.csv
data/processed/fred_real_median_household_income.csv
data/processed/fred_real_disposable_personal_income_per_capita.csv
```

## Reproduce the CBO proxy chart

```bash
python scripts/plot_cbo_proxy.py
```

The chart will be saved to:

```text
outputs/charts/cbo_proxy_median_adjusted_income.png
```

## Reproduce the public proxy comparison chart

```bash
python scripts/plot_public_proxies.py
```

The chart will be saved to:

```text
outputs/charts/public_proxy_comparison.png
```

This chart indexes each series to its first observation. That avoids presenting
different deflator bases as directly comparable dollar levels.

## Current starter files

```text
docs/methodology.md
docs/data_sources.md
src/economics/metrics.py
scripts/plot_cbo_proxy.py
scripts/build_cbo_proxy.py
scripts/build_fred_comparisons.py
scripts/plot_public_proxies.py
data/processed/cbo_proxy_median_adjusted_income_after_tax_transfer.csv
data/processed/fred_real_median_personal_income.csv
data/processed/fred_real_median_household_income.csv
data/processed/fred_real_disposable_personal_income_per_capita.csv
```

## Status

This is a starter scaffold, not a final research product. The CBO proxy is now reproducible from CBO's official researchers ZIP, but the headline metric still needs a custom microdata build before publication-quality interpretation.
