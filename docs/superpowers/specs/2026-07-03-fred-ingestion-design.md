# FRED Comparison Ingestion Design

## Goal

Add reproducible raw-to-processed ingestion for the three public comparison metrics:

- real median personal income, FRED `MEPAINUSA672N`
- real median household income, FRED `MEHOINUSA672N`
- real disposable personal income per capita, FRED `A229RX0`

## Source Contract

The project keeps external downloads manual. Raw files are expected in `data/raw/`
using the existing documented filenames:

```text
data/raw/fred_real_median_personal_income.csv
data/raw/fred_real_median_household_income.csv
data/raw/fred_real_disposable_personal_income_per_capita.csv
```

The builder accepts either FRED's direct graph CSV format:

```text
observation_date,<FRED_SERIES_ID>
```

or the existing project-friendly format:

```text
year,value
```

FRED exports with `DATE,<FRED_SERIES_ID>` or `DATE,value` are also accepted.

## Processing Rules

- Annual FRED/Census median series keep one annual observation per year.
- Monthly real disposable personal income per capita is aggregated to calendar-year means.
- Incomplete monthly years are excluded by default.
- Missing FRED values represented as `.` are dropped.
- Processed outputs use `year`, `value`, `series_id`, `series`, `source`, and `notes` columns.

## Implementation

Add a focused `economics.fred` module with:

- a `FredSeriesSpec` dataclass
- a `FRED_SERIES` registry
- `build_fred_series(raw_csv_path, spec)`
- `build_all_fred_series(raw_dir, processed_dir)`

Add a CLI script:

```bash
python scripts/build_fred_comparisons.py
```

The script reads the three documented raw files and writes processed comparison CSVs.

## Non-Goals

- No automatic network downloads in project code.
- No FRED API key dependency.
- No inflation rebasing across series in this step; units are documented in metadata.
