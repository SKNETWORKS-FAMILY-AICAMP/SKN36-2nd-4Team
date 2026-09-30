"""Export policy-based LoL customer cohorts from the existing SQLite snapshot.

No model is trained. The database and source CSV files are opened read-only.
Run: python -m data_pipeline.prepare_core_cohorts
"""

import sqlite3

import pandas as pd

from data_pipeline.paths import CUTOFF, DB, DERIVED as OUTPUT
MIN_PREVIOUS_30D_GAMES = 4


def assign_cohort(frame: pd.DataFrame) -> pd.Series:
    """Use only features available at cutoff; never use churn for eligibility."""
    established = frame["games_prev30d"].ge(MIN_PREVIOUS_30D_GAMES)
    active = frame["games_30d"].gt(0)
    cohort = pd.Series("limited_prior_activity", index=frame.index, dtype="string")
    cohort.loc[established & ~active] = "previously_active_now_dormant"
    cohort.loc[established & active] = "established_active"
    return cohort


def load_snapshot() -> pd.DataFrame:
    if not DB.is_file():
        raise FileNotFoundError(DB)
    with sqlite3.connect(f"file:{DB.resolve().as_posix()}?mode=ro", uri=True) as conn:
        frame = pd.read_sql_query(
            "SELECT f.*, t.churn FROM ml_features f "
            "JOIN targets t ON t.team_id=f.team_id AND t.player_id=f.player_id "
            "AND t.cutoff_date=f.cutoff_date WHERE f.cutoff_date=?",
            conn, params=(CUTOFF,),
        )
    if frame.duplicated(["team_id", "player_id", "cutoff_date"]).any():
        raise ValueError("Duplicate user/cutoff keys")
    if frame["churn"].isna().any() or not frame["churn"].isin([0, 1]).all():
        raise ValueError("Missing or invalid churn labels")
    return frame


def main() -> None:
    frame = load_snapshot()
    frame.insert(3, "customer_cohort", assign_cohort(frame))
    OUTPUT.mkdir(parents=True, exist_ok=True)
    cohort_path = OUTPUT / f"customer_cohorts_{CUTOFF}.csv"
    core_path = OUTPUT / f"established_active_ml_{CUTOFF}.csv"
    frame.to_csv(cohort_path, index=False, encoding="utf-8-sig")
    core = frame.loc[frame.customer_cohort.eq("established_active")].copy()
    core.to_csv(core_path, index=False, encoding="utf-8-sig")
    counts = frame.groupby("customer_cohort", sort=True)["churn"].agg(
        users="size", no_match_next_30d="sum", observed_rate="mean")
    print(counts.to_string(float_format=lambda x: f"{x:.4f}"))
    print(f"Saved: {cohort_path}")
    print(f"Saved: {core_path}")


if __name__ == "__main__":
    main()
