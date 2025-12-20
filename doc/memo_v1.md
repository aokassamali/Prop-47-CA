# Memo v1 — Prop 47 and reported theft in California (Synthetic Control, 2010–2024)

## Research question
Did California’s Proposition 47 (effective **Nov 2014**) increase reported theft rates in California relative to a synthetic control built from other U.S. states?

## Outcome(s)
- **Primary:** `theft_per_100k_coveredpop` (state-month theft per 100k, scaled by “covered population” to address incomplete monthly reporting).
- **Negative control:** `violent_per_100k_coveredpop` (violent crime per 100k, similarly constructed).

## Data
Monthly UCR-style “offenses known” data aggregated to **state-month**.
Key processing choices:
- Compute `covered_pop = population × 1{month reported}` at the agency-month level; aggregate to state-month.
- Compute `coverage_rate = covered_pop / total_pop` per state-month.
- Exclude states/territories with low or unstable coverage in the pre-period (see `docs/data_qc_report.md` for the exclusion list and rationale).

## Estimand
For treated unit CA and month *t*, let:
- \(Y_{CA,t}(1)\) be the observed outcome under Prop 47.
- \(Y_{CA,t}(0)\) be the counterfactual outcome had Prop 47 not occurred.

The estimand is the post-treatment average treatment effect on the treated (ATT) over a post window \(\mathcal{T}_{post}\):
\[
ATT = \frac{1}{|\mathcal{T}_{post}|}\sum_{t \in \mathcal{T}_{post}} \left(Y_{CA,t}(1) - Y_{CA,t}(0)\right).
\]

## Identification strategy
Use **Synthetic Control (SCM)** to estimate \(Y_{CA,t}(0)\) as a convex combination of donor states:
\[
\hat{Y}_{CA,t}(0)=\sum_{j \in \mathcal{D}} w_j Y_{j,t},\quad w_j\ge 0,\ \sum_j w_j=1
\]
Weights \(w\) minimize squared pre-treatment prediction error over the pre-period.

### Assumptions (informal)
- A weighted average of donor states can approximate CA’s pre-treatment outcome path.
- No other CA-specific shocks at **Nov 2014** that differentially affect the outcome versus donors (or such shocks are small relative to the signal).

## Implementation details
- Fit weights on **2010-01 to 2019-12** (pre-COVID fit window), and evaluate through **2024-12** for descriptive post-COVID patterns.
- Post windows:
  - **Post1:** from treatment month (e.g., 2014-11) through 2019-12
  - **COVID:** 2020-03 to 2021-12 (descriptive only)
  - **Post2:** 2022-01 to 2024-12 (descriptive only)
- Inference: **in-space placebos** (each donor treated in turn) filtered by pre-fit RMSPE:
  - keep placebo *j* if `pre_rmspe_j ≤ m × pre_rmspe_CA` (m in {2.0, 1.5})
  - p-value computed as a finite-sample tail probability on the post/pre RMSPE ratio.

## Main results (state-level)
Across reasonable treatment timing and pre-window choices:
- The treated-minus-synthetic **gap** for theft is generally **positive post-treatment**, but **placebo p-values are not small** in the main post1 window (i.e., CA does not look like an extreme outlier relative to filtered placebos).
- Negative control (violent crime) does not show a consistent, statistically distinctive post-treatment divergence.

Interpretation: at the **state** level, Prop 47 is consistent with a **directional increase** in reported theft, but the magnitude is **not extreme** relative to comparable states once we condition on a good pre-fit.

## Why this can diverge from post-2020 “urban retail collapse” anecdotes
- The state-level series averages over heterogeneous county/city dynamics; a sharp SF/LA core shock can wash out statewide.
- “Retail apocalypse” narratives may reflect *commercial vacancy*, *foot-traffic collapse*, enforcement priorities, and reporting behavior, not just the UCR theft series.
- COVID is a nationwide structural break that complicates attributing 2022–2024 differences to a 2014 policy.

## Limitations
- Coverage / reporting varies across agencies and over time; “covered population” helps but does not eliminate compositional shifts.
- Theft definitions and reporting practices can change; UCR to NIBRS transitions may affect comparability.
- SCM captures deviations from a donor-weighted baseline, not necessarily causal mechanisms.

## Bottom line
This project provides a reproducible, transparent SCM analysis at the **state** level. The evidence supports a modest directional post-Prop47 increase in reported theft, but not a large, uniquely Californian divergence relative to well-fitting donor placebos.

## Repo pointers
- Notebook replication: `notebooks/Prop47_FinalReplication_Clean.ipynb`
- Outputs: `outputs/figures/`, `outputs/tables/`
- Processing notes: `docs/data_processing.md`
- QC rationale: `docs/data_qc_report.md`
- Robustness menu: `docs/robustness_menu.md`
