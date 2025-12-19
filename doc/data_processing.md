# Data Processing Notes

## Goal
Construct a state-month panel (2010-01 to 2019-12) for:
- theft rate per 100k (primary)
- violent crime rate per 100k (negative control)
with explicit handling of reporting coverage/missingness.

## Raw inputs
- Source: Jacob Kaplan UCR compilation (agency-level monthly files), 2010–2019.
- Key fields used:
  - agency identifier: `ORI` (string)
  - geography: `state_abb` (and other FIPS fields retained as metadata)
  - time: `year`, `month`
  - outcomes: theft total, violent total
  - population: agency population
  - reporting metadata:
    - 2010–2019: `number_of_months_reported`

## Agency identity (critical bug + fix)
### Problem encountered
- Using `agency_name` caused collisions: multiple distinct agencies share the same name.
- `ORI9` was missing for some agencies, leading to `None` keys and false duplicates.
- 'number_of_months_missing' indicator is no longer used from 2017-2019 causing issues when concatenating data 

### Fix
- 'number_of_months_reported' is consistent across all files, use inplace of 'number_of_months_missing'
- Use `ORI` (state abbrev + 5 digits) as primary `agency_id`.
- Treat `agency_id` as a string, never numeric.
- Enforce grain assertions:
  - Expected grain: [one row per agency-month OR one row per agency-month-offense]
  - Assertions:
    - no missing `agency_id`
    - no duplicated keys at the chosen grain

## Month-level reporting (missingness harmonization)
### Column changes by year
- 2010–2019: `number_of_months_reported`

### Standardization approach
- Create a unified month-level indicator `reported_{agency,month}` using reconstructed missing-month flags.
- Rule:
  - If a month is flagged missing for an agency-year, exclude that agency-month from aggregation.
  - True zeros are retained (reported month with 0 crimes is not treated as missing).

## Aggregation to state-month
For each state-month:
- `theft_count` = sum(theft_total over included agency-months)
- `violent_count` = sum(violent_total over included agency-months)
- `pop_covered` = sum(pop over included agency-months)
- Rates:
  - `theft_rate_per_100k` = theft_count / pop_covered * 100000
  - `violent_rate_per_100k` = violent_count / pop_covered * 100000
- Coverage:
  - `coverage` = pop_covered / state_total_pop
  - Note: state_total_pop is computed as sum of agency populations

## Output artifacts
- `data/processed/state_month.parquet`
- `outputs/tables/qc_state_coverage_summary.csv`
- `outputs/tables/qc_state_corr_summary_pre.csv`
- `outputs/figures/coverage_CA.png`

## Known limitations
- Outcome is *recorded crime in reporting agencies*, not true incidence.
- Reporting completeness varies by state and time; coverage diagnostics are included.
