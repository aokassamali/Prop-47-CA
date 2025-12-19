# Robustness Menu (pre-registered)

## Baseline specification (S0)
- Unit: state-month, 2010-01 to 2019-12
- Treated unit: California
- Outcome: theft_rate_per_100k
- Treatment start (t0): 2014-11
- Pre-period: 2010-01 to month < t0
- Post-period: month >= t0
- Donor pool: all non-CA states passing data quality screen (see DQ)
- SCM objective: minimize pre-period squared error with constraints w>=0, sum(w)=1
- Primary diagnostic: pre-RMSPE, post/pre RMSPE ratio, placebo p-value (ratio)

## Data quality screen (DQ)
- Exclude donor states with missing outcome in > 0% of pre-period months (strict) 
  [OR > 5% (practical)]
- (TBD) Exclude donor states with known structural breaks documented in notes.

## Robustness checks
Each check reports:
- top donor weights
- pre-RMSPE
- post/pre RMSPE ratio
- placebo p-value (ratio)
- plot: treated vs synthetic + gaps

| ID | Change from baseline | Purpose | Expected pattern if effect is real |
|----|----------------------|---------|-----------------------------------|
| T1 | t0 = 2015-01         | Treatment timing sensitivity | Similar sign/timing; magnitude may shift slightly |
| P1 | pre starts 2012-01   | Reduce reliance on early years | Similar sign; pre-fit should remain good |
| O1 | outcome = violent_rate_per_100k | Negative control | No comparable post-gap; placebos not extreme |
| S1 | treated = CA excluding LA (if constructible) | Check LA reporting drives result | Effect persists if not LA-driven |
| D1 | donor pool excludes high-missing states at >5% | Donor quality sensitivity | Results not driven by bad donors |

## Decision rule / interpretation
- A result is considered "robust" if:
  - pre-RMSPE remains acceptably low across checks, AND
  - CA remains in the extreme tail of placebo ratios (e.g., p < 0.10) in most checks, AND
  - negative control (O1) does not show a similar pattern.
