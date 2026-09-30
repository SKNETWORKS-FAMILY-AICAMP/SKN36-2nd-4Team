"""Build a separate, policy-defined cohort/segment DB without fitting a model.

Reads the canonical SQLite snapshot only. Writes new derived CSVs and a new
SQLite database; never changes the source DB, final CSVs, or merged-team files.
"""

from pathlib import Path
import sqlite3

import pandas as pd

from data_pipeline.prepare_core_cohorts import CUTOFF, DB, OUTPUT, assign_cohort


DEST = DB.with_name(f"core_segments_{CUTOFF}.db")
KEY = ["team_id", "player_id", "cutoff_date"]
MIN_MODE_GAMES = 5
MODE_SHARE = 0.60
ACTIVITY_DROP_RATIO = 0.50
ACTIVITY_GROWTH_RATIO = 1.50


def segment_users(frame: pd.DataFrame) -> pd.DataFrame:
    """Assign non-causal, cutoff-time labels on two independent axes."""
    result = frame.copy()
    result["customer_cohort"] = assign_cohort(result)
    result["play_style"] = "insufficient_recent_games"
    core = result.customer_cohort.eq("established_active")
    enough = core & result.games_30d.ge(MIN_MODE_GAMES)
    result.loc[enough, "play_style"] = "mixed_or_other"
    result.loc[enough & result.ranked_solo_ratio_30d.ge(MODE_SHARE), "play_style"] = "ranked_solo_focused"
    casual_share = result[["normal_ratio_30d", "aram_ratio_30d", "arena_ratio_30d", "rotating_ratio_30d"]].sum(axis=1)
    result.loc[enough & casual_share.ge(MODE_SHARE), "play_style"] = "casual_focused"

    result["activity_trend"] = "not_assessed"
    result.loc[core, "activity_trend"] = "roughly_stable"
    ratio = result.games_30d / result.games_prev30d
    result.loc[core & ratio.le(ACTIVITY_DROP_RATIO), "activity_trend"] = "activity_declining"
    result.loc[core & ratio.ge(ACTIVITY_GROWTH_RATIO), "activity_trend"] = "activity_growing"
    return result


def build() -> tuple[pd.DataFrame, pd.DataFrame]:
    if DEST.exists():
        raise FileExistsError(f"Will not overwrite existing derived DB: {DEST}")
    with sqlite3.connect(f"file:{DB.resolve().as_posix()}?mode=ro", uri=True) as source:
        features = pd.read_sql_query("SELECT * FROM ml_features WHERE cutoff_date=?", source, params=(CUTOFF,))
        labels = pd.read_sql_query("SELECT team_id,player_id,cutoff_date,churn FROM targets WHERE cutoff_date=?", source, params=(CUTOFF,))
    if features.duplicated(KEY).any() or labels.duplicated(KEY).any():
        raise ValueError("Duplicate user/cutoff key in source")
    frame = features.merge(labels, on=KEY, validate="one_to_one")
    if len(frame) != len(features) or frame.churn.isna().any():
        raise ValueError("Missing target for one or more users")
    segmented = segment_users(frame)
    core = segmented.loc[segmented.customer_cohort.eq("established_active")].copy()
    if core.empty:
        raise ValueError("No eligible core users")

    OUTPUT.mkdir(parents=True, exist_ok=True)
    all_csv = OUTPUT / f"customer_segments_{CUTOFF}.csv"
    core_csv = OUTPUT / f"established_active_segmented_ml_{CUTOFF}.csv"
    for path in (all_csv, core_csv):
        if path.exists():
            raise FileExistsError(f"Will not overwrite existing derived CSV: {path}")
    segmented.to_csv(all_csv, index=False, encoding="utf-8-sig")
    core.to_csv(core_csv, index=False, encoding="utf-8-sig")

    # Labels live in a separate table so a training query must join explicitly.
    membership = segmented[KEY + ["customer_cohort", "play_style", "activity_trend"]]
    core_features = core.drop(columns=["customer_cohort", "play_style", "activity_trend", "churn"])
    core_targets = core[KEY + ["churn"]]
    try:
        with sqlite3.connect(DEST) as target:
            membership.to_sql("cohort_membership", target, index=False, if_exists="fail")
            core_features.to_sql("core_ml_features", target, index=False, if_exists="fail")
            core_targets.to_sql("core_targets", target, index=False, if_exists="fail")
            target.execute("CREATE UNIQUE INDEX cohort_user_key ON cohort_membership(team_id,player_id,cutoff_date)")
            target.execute("CREATE UNIQUE INDEX core_feature_key ON core_ml_features(team_id,player_id,cutoff_date)")
            target.execute("CREATE UNIQUE INDEX core_target_key ON core_targets(team_id,player_id,cutoff_date)")
            target.execute("CREATE INDEX cohort_segment_idx ON cohort_membership(customer_cohort,play_style,activity_trend)")
    except Exception:
        # Keep any failed output visible for diagnosis; do not alter source data.
        raise
    print(f"Cohorts: {segmented.customer_cohort.value_counts().to_dict()}")
    print(f"Core styles: {core.play_style.value_counts().to_dict()}")
    print(f"Core trends: {core.activity_trend.value_counts().to_dict()}")
    print(f"Saved: {DEST}, {all_csv}, {core_csv}")
    return segmented, core


if __name__ == "__main__":
    build()
