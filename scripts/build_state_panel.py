from __future__ import annotations

import argparse
from pathlib import Path
import pandas as pd
import numpy as np

COLUMNS = [
    "state_abb",
    "ori",
    "year",
    "month",
    "number_of_months_reported",
    "population",
    "actual_theft_total",
    "actual_index_violent",
]

MISSING_TOKENS = {"", "none", "nan", "null"}


def flag_missing(group: pd.DataFrame) -> pd.DataFrame:
    """
    Uses number_of_months_reported to mark n_missing months as missing.
    Assumption: the 'missing' months are the lowest-crime months in that ORI-year.
    """
    n_missing = int(12 - group["number_of_months_reported"].iloc[0])
    n_missing = max(0, min(n_missing, len(group)))

    group = group.sort_values(["actual_theft_total", "actual_index_violent"], ascending=True).copy()
    group["month_missing"] = False
    if n_missing > 0:
        group.iloc[:n_missing, group.columns.get_loc("month_missing")] = True
    return group


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--raw-dir", type=str, required=True, help="Directory containing offenses_known_monthly_{year}.parquet")
    p.add_argument("--out", type=str, default="data/processed/state_month_covered.parquet")
    p.add_argument("--start-year", type=int, default=2010)
    p.add_argument("--end-year", type=int, default=2024)
    p.add_argument("--drop-states", type=str, default="AR,HI,IN,MI,MS,MT,NE,NH,NY,OH,PA,SD,UT,WV,OR,CZ,PR,GU")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    raw_dir = Path(args.raw_dir)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    drop_states = {s.strip() for s in args.drop_states.split(",") if s.strip()}

    frames = []
    for year in range(args.start_year, args.end_year + 1):
        fp = raw_dir / f"offenses_known_monthly_{year}.parquet"
        if not fp.exists():
            raise FileNotFoundError(f"Missing file: {fp}")

        df = pd.read_parquet(fp, columns=COLUMNS)

        s = df["state_abb"].astype("string").str.strip()
        s_lower = s.str.lower()

        bad = (
            s.isna()
            | s_lower.isin(MISSING_TOKENS)
            | s.isin(drop_states)
        )
        df = df.loc[~bad].copy()

        df = df.groupby(["ori", "year"], group_keys=False).apply(flag_missing)
        frames.append(df)

    state_month = pd.concat(frames, ignore_index=True)

    # date parsing (handles either month names or month numbers)
    if np.issubdtype(state_month["month"].dtype, np.number):
        month_num = state_month["month"].astype(int)
        state_month["date"] = pd.to_datetime(
            state_month["year"].astype(int).astype(str) + "-" + month_num.astype(str).str.zfill(2) + "-01"
        )
    else:
        state_month["date"] = pd.to_datetime(
            state_month["year"].astype(int).astype(str) + " " + state_month["month"].astype(str),
            format="%Y %B",
            errors="coerce",
        )
        state_month["date"] = state_month["date"].dt.to_period("M").dt.to_timestamp()

    # covered population
    state_month["pop_covered"] = state_month["population"] * (~state_month["month_missing"]).astype(int)

    # aggregate
    out = (
        state_month
        .groupby(["state_abb", "date"], as_index=False)
        .agg(
            total_pop=("population", "sum"),
            covered_pop=("pop_covered", "sum"),
            theft=("actual_theft_total", "sum"),
            violent=("actual_index_violent", "sum"),
        )
    )

    out["coverage_rate"] = out["covered_pop"] / out["total_pop"]

    # safe rates (avoid inf)
    out["theft_per_100k_coveredpop"] = np.where(
        out["covered_pop"] > 0,
        (out["theft"] / out["covered_pop"]) * 100000.0,
        np.nan,
    )
    out["violent_per_100k_coveredpop"] = np.where(
        out["covered_pop"] > 0,
        (out["violent"] / out["covered_pop"]) * 100000.0,
        np.nan,
    )

    out.to_parquet(out_path, index=False)
    print(f"Wrote: {out_path}  rows={len(out):,}  states={out['state_abb'].nunique():,}")


if __name__ == "__main__":
    main()
