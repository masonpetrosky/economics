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

Expected starter raw IPUMS export:

```text
data/raw/ipums_cps_asec_raw.csv
```

This file should be a CSV produced after reading the IPUMS extract with the
provided command file or an equivalent conversion step.

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

Starter raw IPUMS bridge columns:

```text
YEAR
SERIAL
PERNUM
AGE
ASECWT
NUMPREC
HHINCOME
CAPGAIN
FEDTAX
FICA
STATETAX
```

Mapping into the normalized contract:

| Normalized column | Starter IPUMS source | Notes |
| --- | --- | --- |
| `year` | `YEAR - 1` | IPUMS ASEC `YEAR` is the survey year; income variables refer to the previous calendar year. |
| `serial` | `SERIAL` | With `YEAR` and `PERNUM`, identifies a person record in the rectangularized extract. |
| `pernum` | `PERNUM` | Person number within household. |
| `age` | `AGE` | Used for adult-only sensitivity filters. |
| `asecwt` | `ASECWT` | Person-level ASEC weight. |
| `household_size` | `NUMPREC` | Number of person records in the household. |
| `money_income` | `HHINCOME` | Total household money income. |
| `realized_capital_gains` | `CAPGAIN` | Tax-model capital gains amount. |
| `noncash_benefits` | none in starter bridge | Filled with `0.0` until a reviewed benefit mapping is added. |
| `health_insurance_value` | none in starter bridge | Filled with `0.0` until a reviewed health-benefit valuation is added. |
| `federal_income_taxes` | `FEDTAX` | Federal income tax liability before credits. |
| `payroll_taxes` | `FICA` | Social Security payroll deduction. |
| `state_local_income_taxes` | `STATETAX` | State income tax liability before credits. |

The normalizer treats the documented IPUMS not-in-universe codes for `HHINCOME`,
`CAPGAIN`, `FEDTAX`, `FICA`, and `STATETAX` as missing values before the
estimator filters invalid rows. It does not treat top-coded values as missing.

Relevant IPUMS documentation:

- Person keys: https://cps.ipums.org/cps-action/faq
- `ASECWT`: https://cps.ipums.org/cps-action/variables/ASECWT
- `NUMPREC`: https://cps.ipums.org/cps-action/variables/NUMPREC
- `HHINCOME`: https://cps.ipums.org/cps-action/variables/HHINCOME
- `CAPGAIN`: https://cps.ipums.org/cps-action/variables/CAPGAIN
- `FEDTAX`: https://cps.ipums.org/cps-action/variables/FEDTAX
- `FICA`: https://cps.ipums.org/cps-action/variables/FICA
- `STATETAX`: https://cps.ipums.org/cps-action/variables/STATETAX

Future work:

- Pull annual ASEC files.
- Build consistent resource-unit records.
- Allocate household resources to persons.
- Add reviewed noncash benefit and health-insurance valuation.
- Review federal, payroll, and state/local tax treatment before interpreting trends.
- Calculate weighted medians by year.
