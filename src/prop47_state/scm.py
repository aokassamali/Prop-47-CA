from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any

import numpy as np
import pandas as pd
import cvxpy as cp
import matplotlib.pyplot as plt


# -----------------------------
# Config defaults (override in scripts)
# -----------------------------
STATE_COL = "state_abb"
DATE_COL = "date"

COVID_START = pd.Timestamp("2020-03-01")
COVID_END   = pd.Timestamp("2021-12-01")
POST2_START = pd.Timestamp("2022-01-01")


def mstart(x) -> pd.Timestamp:
    return pd.to_datetime(x).to_period("M").to_timestamp()


def normalize_panel_df(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = df.columns.astype(str).str.strip()
    df[DATE_COL] = pd.to_datetime(df[DATE_COL]).dt.to_period("M").dt.to_timestamp()
    return df


def build_wide(df: pd.DataFrame, states: List[str], outcome: str,
               date_min: pd.Timestamp, date_max: pd.Timestamp) -> pd.DataFrame:
    sub = df[df[STATE_COL].isin(states)].copy()
    Y = (sub.pivot_table(index=DATE_COL, columns=STATE_COL, values=outcome, aggfunc="mean")
           .sort_index())
    return Y.loc[date_min:date_max]


def solve_scm_weights(y_pre: np.ndarray, X_pre: np.ndarray) -> Tuple[np.ndarray, str]:
    """
    Minimize ||y - X w||^2 s.t. w>=0, sum(w)=1.
    Returns (weights, status).
    """
    y_pre = np.asarray(y_pre).reshape(-1)
    X_pre = np.asarray(X_pre)

    if X_pre.ndim != 2:
        raise ValueError(f"X_pre must be 2D, got shape={X_pre.shape}")
    T0, J = X_pre.shape
    if T0 == 0 or J == 0:
        raise ValueError(f"Empty pre matrices: T0={T0}, J={J}")

    if not np.all(np.isfinite(y_pre)) or not np.all(np.isfinite(X_pre)):
        raise ValueError("Non-finite values in pre matrices (NaN/Inf). Clean inputs first.")

    # scale improves numerical stability; doesn't change argmin
    scale = float(np.std(y_pre))
    if not np.isfinite(scale) or scale <= 0:
        scale = 1.0
    y = y_pre / scale
    X = X_pre / scale

    w = cp.Variable(J)
    obj = cp.Minimize(cp.sum_squares(y - X @ w))
    cons = [w >= 0, cp.sum(w) == 1]
    prob = cp.Problem(obj, cons)

    status = "unknown"
    try:
        prob.solve(solver=cp.OSQP, verbose=False, max_iter=200000, eps_abs=1e-8, eps_rel=1e-8)
        status = prob.status
    except Exception:
        prob.solve(solver=cp.SCS, verbose=False, max_iters=200000, eps=1e-6)
        status = prob.status

    if w.value is None:
        raise ValueError(f"SCM optimization failed: status={status}")

    wv = np.array(w.value).reshape(-1)
    wv[wv < 0] = 0.0
    sm = float(wv.sum())
    if sm <= 0:
        raise ValueError("Degenerate weights (sum<=0).")

    return (wv / sm), status


@dataclass
class FitResult:
    treated: str
    outcome: str
    t0: pd.Timestamp
    pre_start: pd.Timestamp
    date_min: pd.Timestamp
    fit_end: pd.Timestamp
    full_end: pd.Timestamp

    donors_requested: List[str]
    donors_complete_pre: List[str]
    donors_active: List[str]

    weights: pd.Series
    solver_status: str

    dates: pd.DatetimeIndex
    y: np.ndarray
    y_synth: np.ndarray
    gap: np.ndarray

    pre_rmspe: float
    post1_rmspe: float
    post2_rmspe: float

    ratio_post1: float
    ratio_post2: float

    avg_gap_post1: float
    avg_gap_covid: float
    avg_gap_post2: float

    n_pre: int
    n_post1: int
    n_covid: int
    n_post2: int


def _segment_stats(dates: pd.DatetimeIndex, gap: np.ndarray,
                   start: pd.Timestamp, end: pd.Timestamp) -> Tuple[float, float, int]:
    mask = (dates >= start) & (dates <= end)
    g = gap[mask]
    g = g[np.isfinite(g)]
    if g.size == 0:
        return (np.nan, np.nan, 0)
    rmspe = float(np.sqrt(np.mean(g**2)))
    avg = float(np.mean(g))
    return (rmspe, avg, int(g.size))


def fit_one(df: pd.DataFrame, treated: str, outcome: str,
            donors: List[str],
            pre_start, t0, date_min, fit_end, full_end,
            min_donors: int = 5) -> FitResult:
    """
    Fit weights using [date_min..fit_end], evaluate across [date_min..full_end].
    Donors must be complete in pre-period (and in the fit window for stability).
    """
    df = normalize_panel_df(df)

    t0 = mstart(t0)
    pre_start = mstart(pre_start)
    date_min = mstart(date_min)
    fit_end = mstart(fit_end)
    full_end = mstart(full_end)

    if not (pre_start < t0):
        raise ValueError(f"Bad window: pre_start={pre_start} must be < t0={t0}")

    states = [treated] + list(donors)

    # Build fit window panel
    Y_fit = build_wide(df, states, outcome, date_min, fit_end)
    if treated not in Y_fit.columns:
        raise ValueError(f"Treated '{treated}' missing from panel (fit window).")

    pre_mask = (Y_fit.index >= pre_start) & (Y_fit.index < t0)
    if int(pre_mask.sum()) == 0:
        raise ValueError("No pre-period rows after date filtering.")

    # treated must be finite in pre
    if not np.all(np.isfinite(Y_fit.loc[pre_mask, treated].to_numpy())):
        raise ValueError("Treated has non-finite values in pre-period (NaN/Inf).")

    # donors complete in pre and fit window (more stable)
    donors_complete = []
    for d in donors:
        if d not in Y_fit.columns:
            continue
        col = Y_fit[d].to_numpy()
        if np.all(np.isfinite(Y_fit.loc[pre_mask, d].to_numpy())) and np.all(np.isfinite(col)):
            donors_complete.append(d)

    if len(donors_complete) < min_donors:
        raise ValueError(f"Too few complete donors in fit window: {len(donors_complete)} (<{min_donors}).")

    y_pre = Y_fit.loc[pre_mask, treated].to_numpy()
    X_pre = Y_fit.loc[pre_mask, donors_complete].to_numpy()

    w, status = solve_scm_weights(y_pre, X_pre)
    w_ser = pd.Series(w, index=donors_complete).sort_values(ascending=False)

    # Keep only active donors (sparse weights are normal)
    active = w_ser[w_ser > 1e-6].index.tolist()
    if len(active) == 0:
        # fall back to all
        active = donors_complete

    # Build full window for evaluation
    Y_full = build_wide(df, [treated] + active, outcome, date_min, full_end)

    # require treated present
    if treated not in Y_full.columns:
        raise ValueError("Treated missing in full window (unexpected).")

    # only evaluate on rows where treated + all active donors are finite
    Y_full2 = Y_full[[treated] + active].dropna(axis=0, how="any")
    dates = Y_full2.index

    y = Y_full2[treated].to_numpy()
    X = Y_full2[active].to_numpy()

    # align weights to active donor order
    w_active = w_ser.reindex(active).fillna(0.0).to_numpy()
    sm = float(w_active.sum())
    if sm <= 0:
        raise ValueError("Degenerate active weight sum.")
    w_active = w_active / sm

    y_synth = X @ w_active
    gap = y - y_synth

    # Segment stats
    pre_rmspe, _, n_pre = _segment_stats(dates, gap, pre_start, t0 - pd.offsets.MonthBegin(0) - pd.offsets.Day(1))
    # easier: define pre_end as last month before t0
    pre_end = (t0 - pd.offsets.MonthBegin(1))
    pre_rmspe, _, n_pre = _segment_stats(dates, gap, pre_start, pre_end)

    post1_rmspe, avg_post1, n_post1 = _segment_stats(dates, gap, t0, fit_end)
    covid_rmspe, avg_covid, n_covid = _segment_stats(dates, gap, COVID_START, COVID_END)
    post2_rmspe, avg_post2, n_post2 = _segment_stats(dates, gap, POST2_START, full_end)

    denom = (pre_rmspe + 1e-12) if np.isfinite(pre_rmspe) else np.nan
    ratio_post1 = float(post1_rmspe / denom) if np.isfinite(post1_rmspe) and np.isfinite(denom) else np.nan
    ratio_post2 = float(post2_rmspe / denom) if np.isfinite(post2_rmspe) and np.isfinite(denom) else np.nan

    return FitResult(
        treated=treated, outcome=outcome, t0=t0, pre_start=pre_start,
        date_min=date_min, fit_end=fit_end, full_end=full_end,
        donors_requested=list(donors),
        donors_complete_pre=list(donors_complete),
        donors_active=list(active),
        weights=pd.Series(w_active, index=active).sort_values(ascending=False),
        solver_status=status,
        dates=dates, y=y, y_synth=y_synth, gap=gap,
        pre_rmspe=float(pre_rmspe),
        post1_rmspe=float(post1_rmspe),
        post2_rmspe=float(post2_rmspe),
        ratio_post1=ratio_post1,
        ratio_post2=ratio_post2,
        avg_gap_post1=float(avg_post1) if np.isfinite(avg_post1) else np.nan,
        avg_gap_covid=float(avg_covid) if np.isfinite(avg_covid) else np.nan,
        avg_gap_post2=float(avg_post2) if np.isfinite(avg_post2) else np.nan,
        n_pre=n_pre, n_post1=n_post1, n_covid=n_covid, n_post2=n_post2,
    )


def placebo_loop(df: pd.DataFrame, treated_res: FitResult,
                 donors_base: List[str],
                 pre_rmspe_mult: float = 2.0,
                 min_donors: int = 5,
                 verbose: bool = False) -> Tuple[pd.DataFrame, pd.DataFrame, float, float]:
    """
    In-space placebos:
      - treat each donor s as treated at same t0 with donors_base \ {s}
      - filter by pre_rmspe <= mult * treated_pre_rmspe
      - compute pvals for ratio_post1 and ratio_post2
    """
    rows = []
    for s in donors_base:
        donors_s = [d for d in donors_base if d != s]
        try:
            res_s = fit_one(
                df, treated=s, outcome=treated_res.outcome, donors=donors_s,
                pre_start=treated_res.pre_start, t0=treated_res.t0,
                date_min=treated_res.date_min, fit_end=treated_res.fit_end, full_end=treated_res.full_end,
                min_donors=min_donors,
            )
            rows.append({
                "state": s,
                "pre_rmspe": res_s.pre_rmspe,
                "ratio_post1": res_s.ratio_post1,
                "ratio_post2": res_s.ratio_post2,
            })
        except Exception as e:
            if verbose:
                print(f"Skipping placebo {s}: {e}")
            continue

    all_df = pd.DataFrame(rows).dropna()
    thr = float(pre_rmspe_mult) * float(treated_res.pre_rmspe)
    filt = all_df[all_df["pre_rmspe"] <= thr].copy()

    def pval(col: str, treated_val: float) -> float:
        vals = filt[col].to_numpy()
        vals = vals[np.isfinite(vals)]
        if vals.size == 0 or not np.isfinite(treated_val):
            return np.nan
        return float((1 + np.sum(vals >= treated_val)) / (1 + vals.size))

    p1 = pval("ratio_post1", treated_res.ratio_post1)
    p2 = pval("ratio_post2", treated_res.ratio_post2)
    return all_df, filt, p1, p2


# -----------------------------
# Plotting helpers
# -----------------------------
def plot_treated_vs_synth(res: FitResult, outpath: Path, title: str) -> None:
    outpath.parent.mkdir(parents=True, exist_ok=True)
    plt.figure()
    plt.plot(res.dates, res.y, label=res.treated)
    plt.plot(res.dates, res.y_synth, label="Synthetic")
    plt.axvline(res.t0, linestyle="--")
    plt.title(title)
    plt.legend()
    plt.tight_layout()
    plt.savefig(outpath, dpi=200)
    plt.close()


def plot_gap(res: FitResult, outpath: Path, title: str) -> None:
    outpath.parent.mkdir(parents=True, exist_ok=True)
    plt.figure()
    plt.plot(res.dates, res.gap)
    plt.axhline(0, linewidth=1)
    plt.axvline(res.t0, linestyle="--")
    plt.title(title)
    plt.tight_layout()
    plt.savefig(outpath, dpi=200)
    plt.close()


def plot_placebo_hist(filt: pd.DataFrame, treated_val: float, col: str,
                      outpath: Path, title: str) -> None:
    outpath.parent.mkdir(parents=True, exist_ok=True)
    vals = filt[col].to_numpy()
    vals = vals[np.isfinite(vals)]
    plt.figure()
    plt.hist(vals, bins=20)
    if np.isfinite(treated_val):
        plt.axvline(treated_val, linestyle="--")
    plt.title(title)
    plt.tight_layout()
    plt.savefig(outpath, dpi=200)
    plt.close()
