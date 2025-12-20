# Prop-47-CA — Synthetic Control on CA Prop 47 (State-Month Panel)

## Question
Did California’s Proposition 47 (effective Nov 2014) change *reported* theft rates relative to a synthetic control built from other U.S. states?

This repo builds a high-coverage state-month panel from agency-level UCR data and estimates the effect using Synthetic Control Methods (SCM) with in-space placebo inference.

## TL;DR results (state-level)
Across multiple reasonable specs (treatment timing + pre-period window + placebo RMSPE filtering), the estimated post-Prop47 theft gap is **directionally positive but not extreme**, and placebo p-values are **not strongly compelling**. Negative-control results (violent crime) do not show a Prop47-specific “shock.”

> Interpretation: at the statewide level, the evidence supports at most a modest effect in recorded theft rates. Localized “downtown retail collapse” dynamics may not be detectable in statewide aggregates.

## Data
**Source:** Jacob Kaplan’s concatenated UCR agency-level monthly files (Return A) from OpenICPSR.  
**Unit of analysis:** state-month (2010-01 to 2019-12 for core analysis; extension through 2024 is reported descriptively with explicit COVID-era segmentation).

### Key construction choices
- **Agency ID:** use `ORI` (string). Do *not* use `agency_name` due to collisions.
- **Reporting completeness:** harmonize month-level “reported” using `number_of_months_reported`.
- **Monthly inclusion rule:** treat *true zeros* as valid reported months; exclude only flagged missing months.
- **Covered-population rates:** compute outcomes using `pop_covered` (sum of agency populations among reporting agency-months).

### Main outcomes
- `theft_per_100k_coveredpop` (primary)
- `violent_per_100k_coveredpop` (negative control)

## Donor pool / data quality
Baseline donor pool excludes:
- states with unstable coverage around treatment (HI, OR)
- non-state / malformed codes present in the data (e.g., PR, GU, CZ, Virgin Islands; and other missing/None codes)
- states with mean pre-period coverage < 0.95

See `docs/data_qc_report.md` for the exact diagnostics and exclusion list.

Robustness donor pool optionally also excludes states where |corr(coverage, theft)| > 0.5 in the pre-period (e.g., TX & AZ).

## Method
### Synthetic control fit
Choose nonnegative donor weights `w` to minimize pre-period squared error:
- constraints: `w >= 0`, `sum(w) = 1`
- outcome fit window: varies by spec

### Inference: in-space placebos + RMSPE filtering
- Refit SCM for each donor state as if treated at the same `t0`
- Filter out placebos with poor pre-fit: `pre_rmspe_placebo <= m * pre_rmspe_CA`
- Compute placebo p-values using post/pre RMSPE ratios

## Specs (core)
- **S0:** theft, t0=2014-11, pre_start=2010-01
- **S1:** theft, t0=2015-01, pre_start=2010-01
- **S2:** theft, t0=2014-11, pre_start=2012-01
- **N0:** violent, t0=2014-11, pre_start=2010-01

(See `docs/robustness_menu.md`.)

## Reproduce
### Run the replication notebook (recommended)
1. Create env (see `environment.yml`)
2. Open `notebooks/final_replication.ipynb`
3. Run all cells to regenerate figures + tables under `outputs/`

### Inputs / outputs
- Input panel (recommended committed): `data/processed/state_month_covered.*`
- Outputs:
  - `outputs/figures/` (treated vs synth, gaps, placebo histograms)
  - `outputs/tables/` (spec summaries, placebo CSVs, weights)

## Repo map
- `notebooks/` replication notebook
- `docs/` memo, QC report, robustness menu, final writeup
- `data/` data notes + processed panel (raw data should not be committed)
- `outputs/` figures + tables

## Citation
If you use this work, please cite the repo (see `CITATION.cff`).

## License
See `LICENSE`.
