# Data Sources

This file lists the source series and datasets discussed so far.

## CBO: Distribution of Household Income

Primary MVP source:

- Source: Congressional Budget Office
- Report: The Distribution of Household Income, 2022
- Coverage: 1979-2022
- Project use: proxy for median comprehensive disposable resources
- Key concept: adjusted household income after transfers and federal taxes
- URL: https://www.cbo.gov/publication/61911

Useful related page:

- Data and supplemental information page: https://www.cbo.gov/publication/62300
- Additional Data for Researchers ZIP: https://www.cbo.gov/system/files/2026-01/61911-additional-data-for-researchers.zip

Notes:

CBO defines income after transfers and taxes as income before transfers and taxes plus means-tested transfers minus federal taxes. CBO's broader distributional framework includes realized capital gains and several transfer/benefit categories. The CBO proxy should be treated as the first benchmark, not the final custom metric.

Expected manual file:

```text
data/raw/61911-additional-data-for-researchers.zip
```

Expected member inside the ZIP:

```text
61911-additional-data-for-researchers/CBO_distribution_household_income_2022_data/households_ranked_by_inc_after_trans_tax_table_04_median_household_income_1979_2022.csv
```

Expected columns in that member:

```text
year
adj_inc_after_transfers_taxes
```

## FRED / Census: Real median personal income

- Series: MEPAINUSA672N
- Name: Real Median Personal Income in the United States
- Source: U.S. Census Bureau via FRED
- Frequency: Annual
- Units: 2024 C-CPI-U dollars
- URL: https://fred.stlouisfed.org/series/MEPAINUSA672N

Project use:

A clean individual-level comparison series. It is useful because it avoids household-composition distortions, but it is pretax and excludes major noncash benefits.

Expected manual file:

```text
data/raw/fred_real_median_personal_income.csv
```

Expected columns for project import use either the direct FRED graph export:

```text
observation_date
MEPAINUSA672N
```

or the project-shaped format:

```text
year
value
```

## FRED / Census: Real median household income

- Series: MEHOINUSA672N
- Name: Real Median Household Income in the United States
- Source: U.S. Census Bureau via FRED
- Frequency: Annual
- URL: https://fred.stlouisfed.org/series/MEHOINUSA672N

Project use:

A familiar benchmark, but not the preferred headline because household composition changes over time.

Expected manual file:

```text
data/raw/fred_real_median_household_income.csv
```

Expected columns for project import use either the direct FRED graph export:

```text
observation_date
MEHOINUSA672N
```

or the project-shaped format:

```text
year
value
```

## FRED / BEA: Real disposable personal income per capita

- Series: A229RX0
- Name: Real Disposable Personal Income: Per Capita
- Source: Bureau of Economic Analysis via FRED
- Frequency: Monthly
- URL: https://fred.stlouisfed.org/series/A229RX0

Project use:

A timely average after-tax purchasing-power benchmark. Not a median. The project
aggregates monthly observations to full calendar-year means and excludes
incomplete monthly years from processed annual outputs.

Expected manual file:

```text
data/raw/fred_real_disposable_personal_income_per_capita.csv
```

Expected columns for project import use either the direct FRED graph export:

```text
observation_date
A229RX0
```

or the project-shaped format:

```text
year
value
```

## Census: Money income definition

- Source: U.S. Census Bureau
- URL: https://www.census.gov/topics/income-poverty/income/about.html

Project use:

Defines the limitations of standard money income. Census money income excludes capital gains, is measured before personal income taxes, and does not reflect noncash benefits such as food stamps/SNAP, health benefits, and subsidized housing.

## Census: Alternative income definitions

- Source: U.S. Census Bureau
- URL: https://www.census.gov/topics/income-poverty/income/about/glossary/alternative-measures.html

Project use:

Documents alternative income definitions that add taxes, earned income credits, realized capital gains/losses, employer-paid health insurance, Medicare/Medicaid valuation, and other noncash benefits.

## CPS ASEC / IPUMS CPS

- Source: IPUMS CPS
- URL: https://cps.ipums.org/cps/

Project use:

Likely long-run microdata source for a custom person-weighted equivalized income measure.

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

Future work:

- Pull annual ASEC files.
- Build consistent resource-unit records.
- Allocate household resources to persons.
- Apply tax and transfer adjustments.
- Calculate weighted medians by year.
