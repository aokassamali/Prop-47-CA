# Data QC Report

## Summary
This document reports coverage and missingness diagnostics used to justify the donor pool and data construction.

## Test A: Coverage stability around treatment
- Treatment timing checked: 2014-11 and 2015-01
- Using Local (12m) discontinuity: mean(coverage[2013-11:2014-10]) vs mean(coverage[2015-2:2016-1])
- Finding:
  - Most states show stable coverage around treatment.
  - Hawaii (HI) shows large swings (~13%) and is excluded from baseline donor pool.
  - Oregon (OR) also shows large swings (~27%) and is excluded from baseline donor poo.

Artifacts:
- `outputs/figures/ca_coverage.png`
- `outputs/figures/stability.png`

## Test B: Donor pool coverage screen
- Rule (baseline): mean_coverage_pre >= 0.95
- Donor count remaining: 36 states (excluding CA)
- Excluded states due to low coverage in pre period:
  -   AR, HI, IN, MI, MS, MT, NE, NH, NY, OH, PA, SD, UT, WV
Artifacts:
- `outputs/tables/mean_coverage_pre.png`

## Test C: Correlation between coverage and outcome (pre-period only)
- Computed: corr(coverage, theft_rate_per_100k) using pre-period months only
- Finding:
  - Only 2 states have abs(corr) > 0.5 (AZ & TX).
- Use:
  - Not used as a data quality exclusion method.
  - Used as robustness donor screen.
Artifacts:
- `outputs/tables/correlation_table.png`

## Conclusion
- Month-level inclusion approach yields high and stable coverage for CA (~99.5% average).
- Baseline donor pool uses pre-period mean coverage threshold and excludes AR, HI, IN, MI, MS, MT, NE, NH, NY, OH, OR, PA, SD, UT, WV.
- Also general exclusion of non US states DC, GU, CZ, Virgin Islands, PR.
