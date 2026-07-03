# Economics MVP Design

## Goal

Build a small, transparent Python data project for tracking "median adult-equivalent comprehensive disposable resources" in the United States, starting with public proxy series before moving toward microdata estimation.

## Scope

This MVP extends the existing starter scaffold rather than replacing it. It will keep the current CBO proxy CSV, README, methodology notes, and plotting script as the seed, then add package structure, loader boundaries, tests, and a starter notebook.

The bundled CBO proxy data remains a starter series that must be verified against the official CBO supplemental workbook before publication. FRED, Census, CBO workbook, and CPS/IPUMS data handling will be documented through expected filenames and validation helpers, not automated downloads.

## Architecture

The package will use focused modules under `src/economics/`:

- `paths.py`: repo-relative path helpers.
- `loaders.py`: CSV loaders and validation for CBO proxy and future comparison series.
- `equivalence.py`: household-size equivalence scales.
- `resources.py`: broad disposable-resource component model.
- `series.py`: weighted median, growth, inflation/real-series helpers, and compact summaries.
- `charts.py`: matplotlib chart functions.
- `tables.py`: summary-table helpers.

The existing `metrics.py` will remain as a compatibility facade that re-exports the core helpers used by the current plotting script. This avoids breaking the starter script while moving implementation into clearer files.

## Data Flow

The default workflow is:

1. Read starter processed CBO proxy data from `data/processed/cbo_proxy_median_adjusted_income_after_tax_transfer.csv`.
2. Validate required columns and sort by year.
3. Compute one-year, cumulative, and annualized growth.
4. Produce a chart in `outputs/charts/`.
5. Produce compact summary data for README/notebook use.

Future official-source files will live under `data/raw/` with documented expected names and schemas:

- CBO supplemental workbook or exported CSV.
- FRED/Census comparison CSVs for real median personal income, real median household income, and real disposable personal income per capita.
- CPS ASEC/IPUMS extracts for later microdata work.

## Notebook

Add `notebooks/01_cbo_proxy_starter.ipynb`. It will:

- import the package from `src/` without absolute paths,
- load the bundled CBO proxy starter data,
- show a summary table,
- plot the proxy metric using matplotlib,
- state clearly that the bundled CBO values are a starter proxy pending official workbook verification.

## Documentation

Keep the current README and methodology direction, then tighten the workflow documentation around:

- installation with `pip install -e ".[dev]"`,
- expected project structure,
- exact data locations,
- limitations around household composition, taxes, transfers, noncash benefits, realized capital gains, and health-benefit valuation,
- how comparison metrics differ from the headline target.

## Error Handling

Loaders will raise `ValueError` with the missing column names when a file does not match the expected schema. File paths will be passed as `str | Path` and resolved by the caller; no fragile absolute paths will be hard-coded.

## Testing

Add focused pytest coverage for:

- square-root equivalence scaling and invalid household sizes,
- equivalized resources,
- resource component arithmetic,
- weighted median behavior,
- CBO proxy CSV validation,
- growth and summary calculations,
- chart output creation using a temporary directory.

Validation commands for the MVP:

```bash
python -m pytest
python scripts/plot_cbo_proxy.py
```

## Non-Goals

This MVP will not:

- download external datasets automatically,
- claim the bundled CBO starter values are publication-ready,
- implement the CPS/IPUMS microdata estimator,
- choose a final health-benefit valuation method,
- add a heavy orchestration framework before the source files and research questions justify it.
