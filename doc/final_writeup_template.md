# Final writeup template (portfolio report)

> Target length: 4–8 pages in markdown + figures. This is a “paper-style” writeup that a reviewer can skim in 5 minutes.

## 1. Abstract (5–7 sentences)
**Example**
California’s Proposition 47 (effective Nov 2014) reduced penalties for certain theft-related offenses. I evaluate whether California’s reported theft rate increased relative to a synthetic control constructed from other U.S. states using monthly UCR-style “offenses known” data (2010–2024). To address incomplete reporting, I construct a covered-population-adjusted rate and exclude states with poor pre-period coverage. Synthetic control weights are fit on the 2010–2014 (or 2010–2019) pre-period and projected through 2019 (and descriptively through 2024). Across multiple specifications, California’s post-treatment theft gap is generally positive but does not appear extreme versus in-space placebo distributions conditional on good pre-fit. Results for a negative control outcome (violent crime) show no consistent divergence. I discuss measurement limits and why post-2020 urban retail narratives may not map cleanly onto statewide UCR theft trends.

## 2. Background and hypotheses
- What Prop 47 changed, when it started, and the hypothesized mechanism.
- Why we should expect effects in theft specifically (vs violent crime).

**Example paragraph**
Prop 47 reclassified select nonviolent theft and drug possession offenses and reduced penalties below specified thresholds. A standard prediction is that lowering expected punishment for theft can increase the expected return to offending, raising theft incidence and/or reporting. However, the net effect on recorded theft depends on enforcement priorities, reporting incentives, and broader economic conditions. I therefore focus on a design that compares California to a counterfactual trajectory formed from other states with similar pre-2014 theft dynamics.

## 3. Data
- Source(s), unit of observation, time range.
- Coverage issues and your “covered population” approach.
- Exclusions and why.

**Example paragraph**
I use monthly UCR-style “offenses known” data aggregated from agency-month to state-month. A key challenge is incomplete monthly reporting by agencies. I compute covered population as the sum of agency populations for agencies reporting in a given month, and construct theft and violent crime rates per 100k covered population. I exclude states with unstable or low pre-period coverage (mean coverage < 95%) and non-state territories present in the raw files. This yields a balanced donor pool suitable for SCM.

## 4. Estimand
State the estimand formally + define post windows.
Include a short “what would invalidate this” sentence.

## 5. Method
- Synthetic control optimization (constraints).
- In-space placebo inference + RMSPE filtering.
- COVID handling: “fit through 2019, describe after.”

**Example paragraph**
I estimate a synthetic control for California as a convex combination of donor states with nonnegative weights summing to one, chosen to minimize pre-treatment squared error. I assess how unusual the post-treatment divergence is using in-space placebos: each donor is treated in turn with the same intervention date, and I compare California’s post/pre RMSPE ratio to the placebo distribution. To reduce sensitivity to poor-fitting placebos, I filter to donors whose pre-RMSPE is within m× of California’s pre-RMSPE. Because COVID induces a nationwide structural break in recorded crime and reporting, I fit weights through 2019 and report 2022–2024 patterns as descriptive rather than causal.

## 6. Main results
- Show treated vs synthetic plot and gap plot for S0.
- Report summary table across specs (S0/S1/S2) and negative control (N0).
- Interpret p-values carefully (finite-sample placebo p-values, not classical tests).

**Example interpretation**
In the baseline specification (treatment Nov 2014; pre period starting Jan 2010), California’s theft series rises above the synthetic control after treatment, producing a post/pre RMSPE ratio around ~2–3. However, California is not an extreme outlier in the filtered placebo distribution (placebo p-values ~0.2–0.4 depending on RMSPE filter tightness). This suggests that while the direction is consistent with an increase, the magnitude is not unusually large relative to other states with similar pre-trends.

## 7. Robustness
Include a compact “robustness menu” with bullets:
- t0 shift (2014-11 vs 2015-01)
- pre-start shift (2010 vs 2012)
- stricter placebo filtering
- donor exclusions / coverage thresholds

## 8. Limitations
- Outcome measurement + reporting behavior
- Aggregation masking city effects
- COVID / structural breaks
- Policy endogeneity / concurrent changes

## 9. Discussion
Connect the empirical result to your broader thesis:
- Distinguish “statewide recorded theft” vs “urban retail conditions”
- Why anecdotes can be true while statewide SCM is modest
- What additional data would move the needle (retail foot traffic, vacancy, call-for-service, arrests/clearances)

## 10. Conclusion
3 bullets:
- What you found
- What you did not find
- What you would do next

## 11. Reproducibility
- `conda env create -f environment.yml`
- where data lives
- which notebook to run
- where outputs are written
