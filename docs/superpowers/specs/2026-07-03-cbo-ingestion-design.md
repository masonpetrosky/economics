# CBO Ingestion Design

## Goal

Replace the CBO proxy's "trust me" starter status with a reproducible raw-to-processed path based on CBO's official 2022 Additional Data for Researchers ZIP.

## Source

CBO's 2022 distribution page lists an "Additional Data for Researchers" ZIP. Inside it, the relevant CSV is:

```text
61911-additional-data-for-researchers/CBO_distribution_household_income_2022_data/households_ranked_by_inc_after_trans_tax_table_04_median_household_income_1979_2022.csv
```

The project proxy uses that file's `adj_inc_after_transfers_taxes` column.

## Implementation

Add a small `economics.cbo` module that reads the ZIP with Python's standard `zipfile` module, validates the expected member and columns, and returns the processed project schema:

```text
year
median_adjusted_income_after_transfers_taxes_2022_dollars
source
notes
```

Add a CLI script that reads the manually downloaded raw ZIP from `data/raw/61911-additional-data-for-researchers.zip` and writes `data/processed/cbo_proxy_median_adjusted_income_after_tax_transfer.csv`.

## Constraints

- Do not commit the raw ZIP; `data/raw/` remains ignored except `.gitkeep`.
- Do not add an Excel dependency.
- Do not download data automatically.
- Keep the existing plot script and notebook behavior unchanged.
- Verify the current processed CSV is reproducible from the official ZIP shape using tests and, when the raw ZIP is available locally, a real build check.
