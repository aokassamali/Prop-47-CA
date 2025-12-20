from __future__ import annotations

import argparse
from pathlib import Path
import sys
import pandas as pd

# allow imports from src/
REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(REPO_ROOT))

from src.prop47_state.scm import (
    fit_one, placebo_loop,
    plot_treated_vs_synth, plot_gap, plot_placebo_hist,
    mstart, normalize_panel_df
)

DEFAULT_SPECS = [
    ("S0", "theft_per_100k_coveredpop", "2014-11-01", "2010-01-01"),
    ("S1", "theft_per_100k_coveredpop", "2015-01-01", "2010-01-01"),
    ("S2", "theft_per_100k_coveredpop", "2014-11-01", "2012-01-01"),
    ("N0", "violent_per_100k_coveredpop", "2014-11-01", "2010-01-01"),
]

DQ_DEFAULT = {"AR","HI","IN","MI","MS","MT","NE","NH","NY","OH","PA","SD","UT","WV","OR","CZ","PR","GU"}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--panel", type=str, default="data/processed/state_month_covered.parquet")
    p.add_argument("--outdir", type=str, default="outputs")
    p.add_argument("--treated", type=str, default="CA")
    p.add_argument("--date-min", type=str, default="2010-01-01")
    p.add_argument("--fit-end", type=str, default="2019-12-01")
    p.add_argument("--full-end", type=str, default="2024-12-01")
    p.add_argument("--pre-mults", nargs="+", type=float, default=[2.0, 1.5])
    p.add_argument("--min-donors", type=int, default=5)
    p.add_argument("--dq-excluded", type=str, default=",".join(sorted(DQ_DEFAULT)))
    p.add_argument("--verbose-placebos", action="store_true")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    panel_path = Path(args.panel)
    outdir = Path(args.outdir)
    fig_dir = outdir / "figures"
    tab_dir = outdir / "tables"
    fig_dir.mkdir(parents=True, exist_ok=True)
    tab_dir.mkdir(parents=True, exist_ok=True)

    dq_excluded = {s.strip() for s in args.dq_excluded.split(",") if s.strip()}

    df = pd.read_parquet(panel_path)
    df = normalize_panel_df(df)
    df = df[~df["state_abb"].isin(dq_excluded)].copy()

    treated = args.treated
    date_min = args.date_min
    fit_end = args.fit_end
    full_end = args.full_end

    all_rows = []

    for spec_id, outcome, t0, pre_start in DEFAULT_SPECS:
        donors = sorted([s for s in df["state_abb"].unique() if s != treated])

        # fit treated once
        tr = fit_one(
            df, treated=treated, outcome=outcome, donors=donors,
            pre_start=pre_start, t0=t0, date_min=date_min, fit_end=fit_end, full_end=full_end,
            min_donors=args.min_donors,
        )

        # save plots
        plot_treated_vs_synth(tr, fig_dir / f"{spec_id}_treated_vs_synth.png",
                              title=f"{spec_id}: {treated} vs Synthetic ({outcome})")
        plot_gap(tr, fig_dir / f"{spec_id}_gap.png",
                 title=f"{spec_id}: Gap ({treated} - Synth) ({outcome})")

        # save weights
        w_out = tr.weights.sort_values(ascending=False).reset_index()
        w_out.columns = ["donor", "weight"]
        w_out.to_csv(tab_dir / f"{spec_id}_weights.csv", index=False)

        # placebo runs for each mult
        for m in args.pre_mults:
            pl_all, pl_filt, p1, p2 = placebo_loop(
                df, treated_res=tr, donors_base=tr.donors_complete_pre,
                pre_rmspe_mult=m, min_donors=args.min_donors, verbose=args.verbose_placebos
            )

            pl_all.to_csv(tab_dir / f"{spec_id}_placebos_all_m{m}.csv", index=False)
            pl_filt.to_csv(tab_dir / f"{spec_id}_placebos_filt_m{m}.csv", index=False)

            # placebo hists
            if len(pl_filt) > 0:
                plot_placebo_hist(pl_filt, tr.ratio_post1, "ratio_post1",
                                  fig_dir / f"{spec_id}_hist_ratio_post1_m{m}.png",
                                  title=f"{spec_id} ratio_post1 (m={m}) p={p1:.3f}")
                plot_placebo_hist(pl_filt, tr.ratio_post2, "ratio_post2",
                                  fig_dir / f"{spec_id}_hist_ratio_post2_m{m}.png",
                                  title=f"{spec_id} ratio_post2 (m={m}) p={p2:.3f}")

            all_rows.append({
                "spec_id": f"{spec_id}_m{m}",
                "outcome": outcome,
                "t0": str(mstart(t0).date()),
                "pre_start": str(mstart(pre_start).date()),
                "date_min": str(mstart(date_min).date()),
                "fit_end": str(mstart(fit_end).date()),
                "full_end": str(mstart(full_end).date()),
                "n_donors_requested": len(donors),
                "n_donors_complete_pre": len(tr.donors_complete_pre),
                "n_donors_active": len(tr.donors_active),
                "pre_rmspe": tr.pre_rmspe,
                "post1_rmspe": tr.post1_rmspe,
                "post2_rmspe": tr.post2_rmspe,
                "ratio_post1": tr.ratio_post1,
                "ratio_post2": tr.ratio_post2,
                "avg_gap_post1": tr.avg_gap_post1,
                "avg_gap_covid": tr.avg_gap_covid,
                "avg_gap_post2": tr.avg_gap_post2,
                "n_months_pre": tr.n_pre,
                "n_months_post1": tr.n_post1,
                "n_months_covid": tr.n_covid,
                "n_months_post2": tr.n_post2,
                "n_placebos": len(pl_all),
                "n_placebos_filtered": len(pl_filt),
                "pre_rmspe_mult": float(m),
                "pval_ratio_post1": p1,
                "pval_ratio_post2": p2,
                "solver_status": tr.solver_status,
            })

    summary = pd.DataFrame(all_rows)
    summary.to_csv(tab_dir / "all_specs_summary.csv", index=False)
    print(f"Wrote: {tab_dir / 'all_specs_summary.csv'}")
    print(summary)


if __name__ == "__main__":
    main()
