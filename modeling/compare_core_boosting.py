"""Compare three boosting families on the same fixed 2,381-user core cohort.

Run from repository root: python -m modeling.compare_core_boosting
This is exploratory 5-fold OOF comparison at one cutoff, not a model
selection audit or forward-time validation.
"""

from __future__ import annotations

import json

import numpy as np
import pandas as pd
from catboost import CatBoostClassifier
from lightgbm import LGBMClassifier
from sklearn.impute import SimpleImputer
from sklearn.model_selection import StratifiedKFold
from xgboost import XGBClassifier

from modeling.reselect_core_features import prepare_features
from modeling.train_core_churn import CUTOFF, FOLDS, MODEL_PARAMS, ROOT, SEED, evaluate, load_core


OUTPUT = ROOT / f"models/core_boosting_comparison_{CUTOFF}"


def make_model(name: str, positive_weight: float, seed: int):
    if name == "CatBoost":
        return CatBoostClassifier(**{**MODEL_PARAMS, "random_seed": seed,
                                     "class_weights": [1.0, positive_weight]})
    if name == "XGBoost":
        return XGBClassifier(
            n_estimators=500, max_depth=4, learning_rate=0.03,
            min_child_weight=5, reg_lambda=5, objective="binary:logistic",
            eval_metric="logloss", scale_pos_weight=positive_weight,
            tree_method="hist", n_jobs=4, random_state=seed,
        )
    if name == "LightGBM":
        return LGBMClassifier(
            n_estimators=500, max_depth=4, num_leaves=15,
            learning_rate=0.03, min_child_samples=20, reg_lambda=5,
            class_weight={0: 1.0, 1: positive_weight},
            verbosity=-1, n_jobs=4, random_state=seed,
        )
    raise ValueError(name)


def main() -> None:
    core = load_core()
    features, aggregate, _ = prepare_features(core)
    x = features[aggregate]
    y = core.churn.to_numpy(dtype=int)
    names = ("CatBoost", "XGBoost", "LightGBM")
    scores = {name: np.full(len(core), np.nan) for name in names}
    splits = StratifiedKFold(n_splits=FOLDS, shuffle=True, random_state=SEED)
    for fold, (train_idx, validation_idx) in enumerate(splits.split(x, y), start=1):
        imputer = SimpleImputer(strategy="median", keep_empty_features=True)
        train = imputer.fit_transform(x.iloc[train_idx])
        validation = imputer.transform(x.iloc[validation_idx])
        train_labels = y[train_idx]
        weight = float((train_labels == 0).sum() / (train_labels == 1).sum())
        for name in names:
            model = make_model(name, weight, SEED + fold)
            model.fit(train, train_labels)
            scores[name][validation_idx] = model.predict_proba(validation)[:, 1]
        print(f"core boosting comparison fold {fold}/{FOLDS}", flush=True)
    rows = []
    metrics = {}
    for name in names:
        if not np.isfinite(scores[name]).all():
            raise ValueError(f"Incomplete OOF scores: {name}")
        result = evaluate(y, scores[name])
        metrics[name] = result
        rows.append({
            "model": name,
            "users": result["users"], "churners": result["churners"],
            "pr_auc_ap": result["pr_auc_ap"], "roc_auc": result["roc_auc"],
            "recall_10": result["top_10pct"]["recall"],
            "precision_10": result["top_10pct"]["precision"],
            "recall_20": result["top_20pct"]["recall"],
            "precision_20": result["top_20pct"]["precision"],
            "f1_20": result["top_20pct"]["f1"],
            "found_20": result["top_20pct"]["found_churn"],
            "false_alarms_20": result["top_20pct"]["false_alarms"],
        })
    OUTPUT.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(OUTPUT / "comparison.csv", index=False)
    oof = core[["team_id", "player_id", "cutoff_date", "churn"]].copy()
    for name in names:
        oof[f"{name.lower()}_oof_score"] = scores[name]
    oof.to_csv(OUTPUT / "oof_predictions.csv", index=False)
    manifest = {
        "cutoff": CUTOFF, "users": len(core), "churners": int(y.sum()),
        "features": aggregate, "feature_count": len(aggregate),
        "models": list(names), "folds": FOLDS, "seed": SEED,
        "split": "Same stratified 5-fold split for every model; no time holdout.",
        "imputation": "Median fitted on each training fold only.",
        "imbalance": "Positive-to-negative inverse prevalence weight computed on each training fold.",
        "hyperparameters": "Fixed modest-depth configurations; not equally tuned or optimized.",
        "limitations": [
            "One cutoff; no independent future-date test.",
            "Comparing and choosing the highest OOF row on the same folds is exploratory.",
            "Different library weighting implementations and fixed parameter choices remain a comparison limitation.",
            "Class-weighted output scores are not calibrated probabilities.",
        ],
    }
    (OUTPUT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    (OUTPUT / "metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
    print(pd.DataFrame(rows)[["model", "pr_auc_ap", "roc_auc", "recall_20", "precision_20"]].to_string(index=False), flush=True)


if __name__ == "__main__":
    main()
