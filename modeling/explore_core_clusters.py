"""Exploratory K-means on established-active users; no churn labels in fitting."""

import json
import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.impute import SimpleImputer
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

from data_pipeline.build_core_segment_db import DEST, KEY


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "models/core_clusters_2026-08-01"
FEATURES = [
    "games_prev30d", "games_30d", "active_days_30d", "days_since_last_game",
    "ranked_solo_ratio_30d", "ranked_flex_ratio_30d", "aram_ratio_30d",
    "normal_ratio_30d", "mode_switch_rate_20", "winrate_20", "avg_kda_20",
]
LOG_FEATURES = ["games_prev30d", "games_30d", "active_days_30d",
                "days_since_last_game", "avg_kda_20"]


def load_data():
    with sqlite3.connect(f"file:{DEST.resolve().as_posix()}?mode=ro", uri=True) as conn:
        features = pd.read_sql_query("SELECT * FROM core_ml_features ORDER BY team_id,player_id", conn)
        labels = pd.read_sql_query("SELECT * FROM core_targets", conn)
    if len(features) != 2381 or features.duplicated(KEY).any():
        raise ValueError("Unexpected core cohort or duplicate key")
    return features.merge(labels, on=KEY, validate="one_to_one")


def matrix(frame):
    values = frame[FEATURES].copy()
    for column in LOG_FEATURES:
        values[column] = np.log1p(values[column].clip(lower=0))
    filled = SimpleImputer(strategy="median").fit_transform(values)
    return StandardScaler().fit_transform(filled)


def main():
    frame = load_data()
    x = matrix(frame)
    search = []
    for k in range(2, 7):
        model = KMeans(n_clusters=k, n_init=20, random_state=42)
        clusters = model.fit_predict(x)
        score = silhouette_score(x, clusters, sample_size=1500, random_state=42)
        search.append({"k": k, "silhouette_sampled": float(score),
                       "sizes": np.bincount(clusters).tolist()})
    chosen = max(search, key=lambda row: row["silhouette_sampled"])["k"]
    fitted = KMeans(n_clusters=chosen, n_init=20, random_state=42)
    frame["cluster"] = fitted.fit_predict(x)
    profile = frame.groupby("cluster")[FEATURES + ["churn"]].agg(
        {**{column: "mean" for column in FEATURES}, "churn": ["size", "sum", "mean"]})
    # Flatten names only for the JSON export; labels are descriptive, not causes.
    profile.columns = [f"{column}_{stat}" for column, stat in profile.columns]
    profile = profile.reset_index()
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "summary.json").write_text(json.dumps({
        "features": FEATURES, "log_transformed": LOG_FEATURES,
        "method": "median imputation + standard scaling + KMeans",
        "silhouette_sample_size": 1500, "tested_k": search, "chosen_k": chosen,
        "selection_note": "Exploratory choice by sampled silhouette on the same dataset",
        "cluster_profiles": profile.to_dict(orient="records"),
        "warning": "Churn was excluded from clustering; rates are retrospective descriptions, not unbiased prediction metrics."
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    frame[KEY + ["cluster"]].to_json(OUT / "membership.jsonl", orient="records",
                                    lines=True, force_ascii=False)
    print("k search:", search)
    print("chosen k:", chosen)
    print(profile[["cluster", "churn_size", "churn_sum", "churn_mean",
                   "games_30d_mean", "ranked_solo_ratio_30d_mean",
                   "aram_ratio_30d_mean", "days_since_last_game_mean"]].to_string(index=False))


if __name__ == "__main__":
    main()
