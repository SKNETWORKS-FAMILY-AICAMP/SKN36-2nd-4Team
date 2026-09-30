"""5-fold experiment for established active users, with leakage-safe sequences.

Usage: python -m modeling.train_core_churn
The one-cutoff model is an experimental candidate, not validated for deployment.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd
from catboost import CatBoostClassifier
from sklearn.metrics import average_precision_score, roc_auc_score
from sklearn.model_selection import StratifiedKFold

from data_pipeline.build_core_segment_db import CUTOFF, DB, DEST, KEY


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / f"models/core_churn_{CUTOFF}"
SEED = 42
FOLDS = 5
EXCLUDE = set(KEY + ["source_batch_id", "actual_history_matches"])
MODEL_PARAMS = dict(iterations=500, depth=4, learning_rate=0.03,
                    l2_leaf_reg=5, loss_function="Logloss", random_seed=SEED,
                    thread_count=4, verbose=False, allow_writing_files=False)


def readonly(path: Path):
    return sqlite3.connect(f"file:{path.resolve().as_posix()}?mode=ro", uri=True)


def load_core():
    with readonly(DEST) as conn:
        features = pd.read_sql_query("SELECT * FROM core_ml_features ORDER BY team_id,player_id", conn)
        targets = pd.read_sql_query("SELECT * FROM core_targets", conn)
        segments = pd.read_sql_query(
            "SELECT team_id,player_id,cutoff_date,play_style,activity_trend "
            "FROM cohort_membership WHERE customer_cohort='established_active'", conn)
    frame = features.merge(targets, on=KEY, validate="one_to_one")
    frame = frame.merge(segments, on=KEY, validate="one_to_one")
    if len(frame) != 2381 or frame.churn.sum() != 363:
        raise ValueError("Core cohort size/labels differ from audited snapshot")
    if frame.duplicated(KEY).any():
        raise ValueError("Duplicate core user key")
    return frame


def end_streak(values, target):
    count = 0
    for value in reversed(values):
        if value != target:
            break
        count += 1
    return count


def sequence_summary(events: pd.DataFrame) -> dict:
    """Numeric features from the retained recent 30 pre-cutoff matches only."""
    all_events = events.sort_values(["event_time", "sequence_index"])
    solo = all_events.loc[all_events.mode_group.eq("RANKED_SOLO")]
    recent = all_events.tail(5)
    previous = all_events.iloc[-10:-5] if len(all_events) >= 10 else all_events.iloc[0:0]
    solo_recent = solo.tail(5)
    solo_previous = solo.iloc[-10:-5] if len(solo) >= 10 else solo.iloc[0:0]

    def mean(section, column):
        return float(section[column].mean()) if len(section) else np.nan

    return {
        "seq_recent5_winrate": mean(recent, "win"),
        "seq_previous5_winrate": mean(previous, "win"),
        "seq_recent5_kda": mean(recent, "kda"),
        "seq_previous5_kda": mean(previous, "kda"),
        "seq_last_win_streak": end_streak(all_events.win.tolist(), 1),
        "seq_last_loss_streak": end_streak(all_events.win.tolist(), 0),
        "solo_recent5_winrate": mean(solo_recent, "win"),
        "solo_previous5_winrate": mean(solo_previous, "win"),
        "solo_recent5_kda": mean(solo_recent, "kda"),
        "solo_previous5_kda": mean(solo_previous, "kda"),
        "solo_last_win_streak": end_streak(solo.win.tolist(), 1),
        "solo_last_loss_streak": end_streak(solo.win.tolist(), 0),
        "solo_matches_in_sequence": len(solo),
    }


def load_sequence_features(core: pd.DataFrame):
    with readonly(DB) as conn:
        events = pd.read_sql_query(
            "SELECT team_id,player_id,cutoff_date,sequence_index,event_time,"
            "mode_group,win,kda FROM sequence_events WHERE cutoff_date=?",
            conn, params=(CUTOFF,))
    events = events.merge(core[KEY], on=KEY, validate="many_to_one")
    events["event_time"] = pd.to_datetime(events.event_time, utc=True, errors="raise")
    cutoff_time = pd.Timestamp(CUTOFF, tz="UTC")
    if events.event_time.ge(cutoff_time).any():
        raise ValueError("Future event reached sequence feature generation")
    if events.duplicated(KEY + ["sequence_index"]).any():
        raise ValueError("Duplicate sequence event")
    rows = []
    for key, group in events.groupby(KEY, sort=False):
        rows.append(dict(zip(KEY, key), **sequence_summary(group)))
    result = pd.DataFrame(rows)
    if len(result) != len(core):
        raise ValueError("Some core users lack a pre-cutoff sequence")
    return result


def ranking_metrics(truth, scores, fraction):
    scores = np.asarray(scores, dtype=float)
    selected = max(1, int(np.ceil(len(truth) * fraction)))
    index = np.argsort(-scores, kind="stable")[:selected]
    found = int(np.asarray(truth)[index].sum())
    positives = int(np.asarray(truth).sum())
    precision = found / selected
    recall = found / positives if positives else np.nan
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {"selected": selected, "found_churn": found,
            "false_alarms": selected - found, "precision": precision,
            "recall": recall, "f1": f1}


def evaluate(truth, scores):
    truth = np.asarray(truth, dtype=int)
    scores = np.asarray(scores, dtype=float)
    return {
        "users": len(truth), "churners": int(truth.sum()),
        "prevalence": float(truth.mean()),
        "pr_auc_ap": float(average_precision_score(truth, scores)),
        "roc_auc": float(roc_auc_score(truth, scores)),
        "top_10pct": ranking_metrics(truth, scores, 0.10),
        "top_20pct": ranking_metrics(truth, scores, 0.20),
    }


def main():
    core = load_core()
    sequence = load_sequence_features(core)
    core = core.merge(sequence, on=KEY, validate="one_to_one")
    baseline = [column for column in core.columns if column not in EXCLUDE
                and column not in {"churn", "play_style", "activity_trend"}
                and not column.startswith(("seq_", "solo_"))]
    added = [column for column in core.columns if column.startswith(("seq_", "solo_"))]
    if not baseline or not added or "churn" in baseline + added:
        raise ValueError("Invalid feature manifest")
    if not all(pd.api.types.is_numeric_dtype(core[column]) for column in baseline + added):
        raise TypeError("All model features must be numeric")
    truth = core.churn.to_numpy(dtype=int)
    splits = list(StratifiedKFold(n_splits=FOLDS, shuffle=True,
                                  random_state=SEED).split(core, truth))
    results = {}
    oof = core[KEY + ["play_style", "activity_trend", "churn"]].copy()
    oof["evaluation_group"] = np.where(
        core.play_style.eq("ranked_solo_focused"), "solo_focused", "other")
    for name, columns in (("baseline_aggregates", baseline),
                          ("with_match_sequence", baseline + added)):
        scores = np.full(len(core), np.nan)
        for fold, (train_idx, val_idx) in enumerate(splits, start=1):
            model = CatBoostClassifier(**MODEL_PARAMS)
            model.fit(core.iloc[train_idx][columns], truth[train_idx])
            scores[val_idx] = model.predict_proba(core.iloc[val_idx][columns])[:, 1]
            print(f"{name}: fold {fold}/{FOLDS} complete", flush=True)
        if not np.isfinite(scores).all():
            raise ValueError("Missing or nonfinite out-of-fold score")
        oof[name] = scores
        results[name] = {"all_core": evaluate(truth, scores)}
        for group in ("solo_focused", "other"):
            mask = oof.evaluation_group.eq(group).to_numpy()
            results[name][group] = evaluate(truth[mask], scores[mask])

    # Prefer the simpler model unless sequence features clearly improve both
    # ranking quality and the budget-based decision metric on the same folds.
    # This rule is exploratory because it was set during this one-cutoff study.
    base_metrics = results["baseline_aggregates"]["all_core"]
    sequence_metrics = results["with_match_sequence"]["all_core"]
    selected = ("with_match_sequence"
                if sequence_metrics["pr_auc_ap"] >= base_metrics["pr_auc_ap"] + 0.01
                and sequence_metrics["top_20pct"]["f1"] >= base_metrics["top_20pct"]["f1"]
                else "baseline_aggregates")
    OUTPUT.mkdir(parents=True, exist_ok=True)
    for name, columns in (("baseline_aggregates", baseline),
                          ("with_match_sequence", baseline + added)):
        model = CatBoostClassifier(**MODEL_PARAMS)
        model.fit(core[columns], truth)
        model.save_model(str(OUTPUT / f"{name}.cbm"))
    oof.to_json(OUTPUT / "oof_predictions.jsonl", orient="records", lines=True, force_ascii=False)
    manifest = {
        "cutoff_date": CUTOFF, "core_definition": "games_prev30d >= 4 and games_30d > 0",
        "label": "no match in any mode during next 30 days",
        "model_family": "CatBoost", "folds": FOLDS, "seed": SEED,
        "parameters": MODEL_PARAMS,
        "features": {"baseline_aggregates": baseline,
                     "with_match_sequence": baseline + added},
        "preferred_candidate_exploratory": selected,
        "selection_rule": "sequence only if OOF AP improves by >=0.01 and top-20% F1 does not fall; otherwise baseline",
        "warnings": ["One cutoff only; no forward-time validation.",
                     "Model selection on these OOF predictions can be optimistic.",
                     "play_style is an evaluation segment, not an input feature.",
                     "Sequence is capped at the latest 30 pre-cutoff games."],
    }
    (OUTPUT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    (OUTPUT / "metrics.json").write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({name: {group: {"ap": round(value["pr_auc_ap"], 4),
                                            "recall20": round(value["top_20pct"]["recall"], 4)}
                              for group, value in groups.items()}
                      for name, groups in results.items()}, indent=2))
    print(f"Exploratory preferred candidate: {selected}; output: {OUTPUT}")


if __name__ == "__main__":
    main()
