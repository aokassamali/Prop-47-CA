# Robustness Menu (Prop 47 SCM)

## Baseline (S0)
- Unit: state-month (2010-01 to 2019-12)
- Treated: California
- Outcomes:
  - Primary: theft_rate_per_100k (constructed using covered population)
  - Negative control: violent_rate_per_100k
- Treatment start options:
  - T0a: 2014-11
  - T0b: 2015-01
- Pre-period options:
  - P0: start 2010-01 to month < t0
  - P1: start 2012-01 to month < t0
- SCM weights: minimize pre-period squared error subject to w>=0, sum(w)=1
- Inference: placebo states + pre-fit (RMSPE) filtering

## Data construction (common to all specs)
### Agency identity & aggregation
- Agency key: ORI (state abbrev + 5 digits). ORI9 missing values caused false duplicates; ORI is complete and unique at the agency-month grain.
- Month-level reporting flags:
  - 2010–2019: use `number_of_months_reported`
  - Standardize to a month-level "reported" indicator using reconstructed missing-month flags.

### Monthly inclusion rule (DQ0 baseline)
- Include agency-month if that month is reported (true zeros retained).
- Exclude only agency-months that are missing (not treated as 0).
- Aggregate to state-month:
  - theft_count = sum(theft_total across included agency-months)
  - pop_covered = sum(pop across included agency-months)
  - theft_rate_per_100k = theft_count / pop_covered * 100000
  - coverage = pop_covered / state_total_pop (or agency-pop total)

## Donor pool rules
### DonorPool0 (baseline)
- Exclude HI (coverage unstable; ~13% swings around treatment date) & OR (coverage unstable; ~27% swings around treatment date)
- Keep states with mean_coverage_pre >= 0.95

### DonorPool1 (robustness)
- DonorPool0 +
- Exclude states with abs(corr(coverage, theft_rate)) > 0.5 in the PRE period only (TX & AZ)

## QC findings to reference
- Test A: all states except HI show stable coverage around treatment date
- Test B: 36 states remain under mean_coverage_pre >= 0.95 (excluding CA)
- Test C: 2 states have abs corr(coverage, theft_rate) > 0.5 (flagged for DonorPool1 robustness)

## Spec checklist (each spec outputs same artifacts)
Each run saves:
- top donor weights
- pre-RMSPE
- post/pre RMSPE ratio
- placebo p-value (ratio)
- plots: treated vs synthetic; gap over time; placebo distribution

| Spec ID | Donor pool | Outcome | t0 | Pre window |
|--------:|------------|---------|----|------------|
| S0      | Pool0      | theft   | 2014-11 | 2010-01 |
| S1      | Pool0      | theft   | 2015-01 | 2010-01 |
| S2      | Pool0      | theft   | 2014-11 | 2012-01 |
| S3      | Pool0      | theft   | 2015-01 | 2012-01 |
| N0      | Pool0      | violent | 2014-11 | 2010-01 |
| D0      | Pool1      | theft   | 2014-11 | 2010-01 |

## Placebo & filtering rule
- Placebo: run SCM for each donor state as if treated at same t0.
- Filter: drop placebo states with pre-RMSPE > 5x CA pre-RMSPE (sensitivity: 2x and 10x).
