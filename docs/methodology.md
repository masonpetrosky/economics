# Methodology

## Goal

Estimate how the typical American's real disposable resources have changed over time.

The conceptual target is not the unemployment rate, job creation, GDP, or raw household income. The target is closer to:

> How much real purchasing power does the median person have after accounting for taxes, transfers, inflation, household size, and income composition?

## Preferred target metric

The preferred long-run metric is:

**Median adult-equivalent comprehensive disposable resources**

For each person, estimate the resources available to their household or resource unit, adjust for household size, and then calculate the median person-weighted value.

A simplified formula:

```text
comprehensive_resources =
    money_income
  + realized_capital_gains
  + noncash_benefits
  + health_insurance_value
  - federal_income_taxes
  - payroll_taxes
  - state_and_local_income_taxes

equivalized_resources = comprehensive_resources / sqrt(household_size)
```

Then:

```text
headline_metric = weighted_median(equivalized_resources, person_weight)
```

## Why person-weighted and equivalized?

Using raw household income over long periods can be misleading because the household unit changes. Fewer people getting married, more people living alone, and changes in household size can reduce measured household income even when individual living standards are improving.

A person-weighted, household-size-adjusted measure asks:

> What resources does the median person have access to, after adjusting for shared living costs?

The square-root scale is a common equivalence adjustment:

```text
adjusted_income = household_income / sqrt(household_size)
```

It assumes that a two-person household needs more than a one-person household, but not exactly twice as much, to reach the same living standard.

## MVP proxy: CBO adjusted income after transfers and taxes

The first version uses CBO's median adjusted household income after transfers and federal taxes.

This proxy is useful because CBO's income concept is broad. It includes market income, realized capital gains, social insurance benefits, means-tested transfers, and federal taxes. It also adjusts for household size.

For this MVP, the bundled processed CBO proxy is an executable starter series rebuilt from CBO's official Additional Data for Researchers ZIP. It is useful for building and testing the workflow, but it should not be treated as the final publication-quality project metric until a custom person-weighted microdata build is added.

Limitations:

- household composition can still differ from the custom person-level CPS/IPUMS build.
- federal taxes versus state/local taxes may differ from the ideal project concept.
- transfers are included through CBO definitions rather than a custom program-level model.
- noncash benefits are included through CBO definitions rather than a custom valuation.
- realized capital gains are included, but sensitivity work should show versions with and without them.
- health-benefit valuation is inherently controversial.
- It ends in 2022 in the current CBO release.
- Pandemic-era years include temporary policy effects that should be labeled clearly.

## Important income concepts

### Census money income

Census money income is before personal income taxes and excludes capital gains and noncash benefits. That makes it a useful but incomplete living-standard measure.

### Real median personal income

Useful because it is individual-level and avoids household-composition problems. But it is still pretax money income and excludes major noncash benefits.

### Real disposable personal income per capita

Useful because it is after-tax, inflation-adjusted, broad, and timely. But it is an average, not a median, so it can be moved by income gains at the top.

For annual comparison charts, the monthly FRED/BEA series is averaged within
complete calendar years. Incomplete current-year observations are excluded until
a full 12 months are available.

### CBO income after transfers and taxes

Useful because it is distributional and comprehensive. It is currently the best public shortcut for this project.

## Public proxy comparison charts

The FRED comparison metrics are included to benchmark trends, not to replace the
project's headline concept. Because the public series use different units and
deflator bases, the comparison chart indexes each series to its first observation
rather than plotting all lines as directly comparable dollar levels.

## Planned sensitivity toggles

The final project should show multiple versions rather than pretending there is one perfect number.

Suggested toggles:

1. Include versus exclude realized capital gains.
2. Include versus exclude health insurance value.
3. CPI-U-RS / C-CPI-U versus PCE deflator.
4. All persons versus adults only.
5. Square-root equivalence scale versus per-capita household split.
6. Federal-only taxes versus federal + state/local taxes.
7. Household ranking versus person-weighted ranking.

## Research questions

1. Has the median person-equivalent comprehensive income grown faster or slower than real median personal income?
2. How much do taxes and transfers change the trend?
3. How much of post-2000 stagnation remains after adding noncash benefits?
4. How much do health-insurance benefits inflate measured living standards without improving spendable cash?
5. How much did temporary pandemic policy raise the median in 2020 and 2021?
6. What explains the gap between average real disposable income per capita and the median person-level measure?
