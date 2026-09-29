"""Re-select core-cohort features and imbalance handling without fold leakage.

Run from the project root: python -m modeling.reselect_core_features

One cutoff is available, so even nested cross-validation is not forward-time
validation. The selected model is an experimental candidate, not a calibrated
churn probability or an operationally validated model.
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd
from catboost import CatBoostClassifier, Pool
from imblearn.over_sampling import RandomOverSampler, SMOTE
from sklearn.impute import SimpleImputer
from sklearn.metrics import average_precision_score
from sklearn.model_selection import StratifiedKFold
from sklearn.preprocessing import StandardScaler

from modeling.train_core_churn import (
    CUTOFF, EXCLUDE, FOLDS, MODEL_PARAMS, ROOT, SEED, evaluate, load_core,
)


OUTPUT = ROOT / f"models/core_reselected_{CUTOFF}"
FEATURE_SETS = ("aggregate33", "engineered40", "shap15")
TREATMENTS = ("none", "class_weight_2", "class_weight_balanced", "ros", "smote")
MODE_SHARES = (
    "ranked_solo_ratio_30d", "ranked_flex_ratio_30d", "normal_ratio_30d",
    "aram_ratio_30d", "arena_ratio_30d", "rotating_ratio_30d",
    "other_ratio_30d",
)


def prepare_features(core: pd.DataFrame) -> tuple[pd.DataFrame, list[str], list[str]]:
    """Only within-person, pre-cutoff arithmetic; never uses churn or IDs."""
    aggregate = [
        col for col in core.columns
        if col not in EXCLUDE | {"churn", "play_style", "activity_trend"}
        and pd.api.types.is_numeric_dtype(core[col])
    ]
    if len(aggregate) != 33:
        raise ValueError(f"Expected 33 original aggregate features, got {len(aggregate)}")
    x = core[aggregate].copy().astype(float)
    x["recent_activity_ratio"] = x.games_30d / (x.games_prev30d + 1.0)
    x["last_week_share"] = x.games_7d / (x.games_30d + 1.0)
    x["games_per_active_day"] = x.games_30d / (x.active_days_30d + 1.0)
    x["last_vs_typical_gap"] = x.days_since_last_game / (x.avg_gap_30d + 1.0)
    x["gap_spread"] = x.max_gap_30d - x.avg_gap_30d
    x["ranked_share"] = x.ranked_solo_ratio_30d + x.ranked_flex_ratio_30d
    x["mode_concentration"] = x[list(MODE_SHARES)].max(axis=1)
    x = x.replace([np.inf, -np.inf], np.nan)
    if len(x.columns) != 40 or x.columns.duplicated().any():
        raise ValueError("Unexpected engineered feature set")
    return x, aggregate, list(x.columns)


def shap_order(x_train: pd.DataFrame, y_train: np.ndarray) -> tuple[list[str], dict[str, float]]:
    """Fit both the imputer and SHAP-ranking model on training users only."""
    imputer = SimpleImputer(strategy="median", keep_empty_features=True)
    array = imputer.fit_transform(x_train)
    model = CatBoostClassifier(**MODEL_PARAMS)
    model.fit(array, y_train)
    pool = Pool(array, label=y_train, feature_names=list(x_train.columns))
    values = model.get_feature_importance(pool, type="ShapValues")[:, :-1]
    mean_abs = np.abs(values).mean(axis=0)
    importance = dict(zip(x_train.columns, map(float, mean_abs)))
    order = sorted(x_train.columns, key=lambda col: (-importance[col], col))
    return order, importance


def columns_for(name: str, aggregate: list[str], engineered: list[str], order: list[str]) -> list[str]:
    return {
        "aggregate33": aggregate,
        "engineered40": engineered,
        "shap15": order[:15],
    }[name]


def fit_model(
    x_train: pd.DataFrame, y_train: np.ndarray, columns: list[str],
    treatment: str, seed: int,
) -> tuple[CatBoostClassifier, SimpleImputer]:
    imputer = SimpleImputer(strategy="median", keep_empty_features=True)
    train = imputer.fit_transform(x_train[columns])
    labels = np.asarray(y_train, dtype=int)
    params = MODEL_PARAMS.copy()
    params["random_seed"] = seed
    if treatment == "class_weight_2":
        params["class_weights"] = [1.0, 2.0]
    elif treatment == "class_weight_balanced":
        params["class_weights"] = [1.0, float((labels == 0).sum() / (labels == 1).sum())]
    elif treatment == "ros":
        train, labels = RandomOverSampler(random_state=seed).fit_resample(train, labels)
    elif treatment == "smote":
        # Distance-based synthesis needs training-only scaling. The inverse
        # transform restores the original units before fitting CatBoost.
        scaler = StandardScaler().fit(train)
        scaled, labels = SMOTE(random_state=seed, k_neighbors=5).fit_resample(
            scaler.transform(train), labels,
        )
        train = scaler.inverse_transform(scaled)
    elif treatment != "none":
        raise ValueError(treatment)
    model = CatBoostClassifier(**params)
    model.fit(train, labels)
    return model, imputer


def fit_predict(
    x_train: pd.DataFrame, y_train: np.ndarray, x_val: pd.DataFrame,
    columns: list[str], treatment: str, seed: int,
) -> np.ndarray:
    model, imputer = fit_model(x_train, y_train, columns, treatment, seed)
    return model.predict_proba(imputer.transform(x_val[columns]))[:, 1]


def inner_select(
    x: pd.DataFrame, y: np.ndarray, aggregate: list[str], engineered: list[str],
    seed: int,
) -> tuple[tuple[str, str], pd.DataFrame]:
    """Choose a configuration using only the enclosing outer-training users."""
    splits = StratifiedKFold(n_splits=3, shuffle=True, random_state=seed)
    results = {f"{features}:{treatment}": [] for features in FEATURE_SETS for treatment in TREATMENTS}
    for inner_fold, (train_idx, val_idx) in enumerate(splits.split(x, y), start=1):
        xt, xv = x.iloc[train_idx], x.iloc[val_idx]
        yt, yv = y[train_idx], y[val_idx]
        order, _ = shap_order(xt, yt)
        for feature_set in FEATURE_SETS:
            columns = columns_for(feature_set, aggregate, engineered, order)
            for treatment in TREATMENTS:
                pred = fit_predict(xt, yt, xv, columns, treatment, seed + inner_fold)
                metric = evaluate(yv, pred)
                results[f"{feature_set}:{treatment}"].append(
                    (metric["pr_auc_ap"], metric["top_20pct"]["f1"]),
                )
    rows = []
    for key, values in results.items():
        feature_set, treatment = key.split(":")
        rows.append({
            "feature_set": feature_set, "treatment": treatment,
            "ap_mean": float(np.mean([value[0] for value in values])),
            "f1_20_mean": float(np.mean([value[1] for value in values])),
        })
    summary = pd.DataFrame(rows).sort_values(
        ["ap_mean", "f1_20_mean", "feature_set", "treatment"],
        ascending=[False, False, True, True],
    )
    winner = summary.iloc[0]
    return (str(winner.feature_set), str(winner.treatment)), summary


def full_candidate_cv(
    x: pd.DataFrame, y: np.ndarray, aggregate: list[str], engineered: list[str],
) -> tuple[pd.DataFrame, dict[str, np.ndarray], dict[str, int]]:
    scores = {f"{features}:{treatment}": np.full(len(x), np.nan)
              for features in FEATURE_SETS for treatment in TREATMENTS}
    frequency: Counter[str] = Counter()
    split = StratifiedKFold(n_splits=FOLDS, shuffle=True, random_state=SEED)
    for fold, (train_idx, val_idx) in enumerate(split.split(x, y), start=1):
        xt, xv = x.iloc[train_idx], x.iloc[val_idx]
        yt = y[train_idx]
        order, _ = shap_order(xt, yt)
        frequency.update(order[:15])
        for feature_set in FEATURE_SETS:
            columns = columns_for(feature_set, aggregate, engineered, order)
            for treatment in TREATMENTS:
                key = f"{feature_set}:{treatment}"
                scores[key][val_idx] = fit_predict(xt, yt, xv, columns, treatment, SEED + fold)
        print(f"full-data candidate CV fold {fold}/{FOLDS}", flush=True)
    rows = []
    for key, values in scores.items():
        if not np.isfinite(values).all():
            raise ValueError(f"Incomplete OOF: {key}")
        feature_set, treatment = key.split(":")
        metrics = evaluate(y, values)
        rows.append({
            "feature_set": feature_set, "treatment": treatment,
            "ap": metrics["pr_auc_ap"], "roc_auc": metrics["roc_auc"],
            "recall_10": metrics["top_10pct"]["recall"],
            "precision_10": metrics["top_10pct"]["precision"],
            "f1_10": metrics["top_10pct"]["f1"],
            "recall_20": metrics["top_20pct"]["recall"],
            "precision_20": metrics["top_20pct"]["precision"],
            "f1_20": metrics["top_20pct"]["f1"],
            "found_20": metrics["top_20pct"]["found_churn"],
            "false_alarms_20": metrics["top_20pct"]["false_alarms"],
        })
    return pd.DataFrame(rows).sort_values(
        ["ap", "f1_20", "feature_set", "treatment"],
        ascending=[False, False, True, True],
    ), scores, dict(frequency)


def write_selected_model_shap(
    model: CatBoostClassifier, imputer: SimpleImputer,
    x: pd.DataFrame, columns: list[str],
) -> None:
    """Explain the actual saved candidate, not the unweighted ranking model."""
    pool = Pool(imputer.transform(x[columns]), feature_names=columns)
    values = model.get_feature_importance(pool, type="ShapValues")[:, :-1]
    pd.DataFrame({
        "feature": columns,
        "mean_abs_shap": np.abs(values).mean(axis=0),
    }).sort_values("mean_abs_shap", ascending=False).to_csv(
        OUTPUT / "selected_model_shap_importance.csv", index=False,
    )


def refresh_selected_model_shap() -> None:
    """Refresh the final-model explanation without repeating nested CV."""
    manifest = json.loads((OUTPUT / "manifest.json").read_text(encoding="utf-8"))
    columns = manifest["selected_features"]
    imputer = SimpleImputer(strategy="median", keep_empty_features=True)
    x, _, _ = prepare_features(load_core())
    imputer.fit(x[columns])
    model = CatBoostClassifier()
    model.load_model(str(OUTPUT / "selected_model.cbm"))
    write_selected_model_shap(model, imputer, x, columns)


def main() -> None:
    core = load_core()
    x, aggregate, engineered = prepare_features(core)
    y = core.churn.to_numpy(dtype=int)
    nested = np.full(len(x), np.nan)
    choices = []
    outer = StratifiedKFold(n_splits=FOLDS, shuffle=True, random_state=SEED)
    for fold, (train_idx, val_idx) in enumerate(outer.split(x, y), start=1):
        xt, xv = x.iloc[train_idx], x.iloc[val_idx]
        yt = y[train_idx]
        (feature_set, treatment), inner = inner_select(
            xt, yt, aggregate, engineered, SEED + fold,
        )
        order, _ = shap_order(xt, yt)
        columns = columns_for(feature_set, aggregate, engineered, order)
        nested[val_idx] = fit_predict(xt, yt, xv, columns, treatment, SEED + fold)
        choices.append({
            "fold": fold, "feature_set": feature_set, "treatment": treatment,
            "inner_ap": float(inner.iloc[0].ap_mean),
        })
        print(f"nested outer fold {fold}/{FOLDS}: {feature_set} + {treatment}", flush=True)
    if not np.isfinite(nested).all():
        raise ValueError("Incomplete nested OOF")

    candidates, scores, shap_frequency = full_candidate_cv(x, y, aggregate, engineered)
    winner = candidates.iloc[0]
    name = f"{winner.feature_set}:{winner.treatment}"
    full_order, full_importance = shap_order(x, y)
    selected_columns = columns_for(str(winner.feature_set), aggregate, engineered, full_order)
    final_model, final_imputer = fit_model(x, y, selected_columns, str(winner.treatment), SEED)

    OUTPUT.mkdir(parents=True, exist_ok=True)
    final_model.save_model(str(OUTPUT / "selected_model.cbm"))
    write_selected_model_shap(final_model, final_imputer, x, selected_columns)
    candidates.to_csv(OUTPUT / "candidate_cv.csv", index=False)
    pd.DataFrame(choices).to_csv(OUTPUT / "nested_fold_choices.csv", index=False)
    pd.DataFrame([
        {"feature": col, "mean_abs_shap": full_importance[col],
         "top15_outer_folds": shap_frequency.get(col, 0)}
        for col in full_order
    ]).to_csv(OUTPUT / "core_shap_importance.csv", index=False)
    oof = core[["team_id", "player_id", "cutoff_date", "churn", "play_style"]].copy()
    oof["nested_selected_score"] = nested
    oof["selected_candidate_oof_score"] = scores[name]
    oof.to_csv(OUTPUT / "oof_predictions.csv", index=False)

    nested_metrics = {"all_core": evaluate(y, nested)}
    selected_metrics = {"all_core": evaluate(y, scores[name])}
    for group, mask in {
        "solo_focused": core.play_style.eq("ranked_solo_focused").to_numpy(),
        "other": core.play_style.ne("ranked_solo_focused").to_numpy(),
    }.items():
        nested_metrics[group] = evaluate(y[mask], nested[mask])
        selected_metrics[group] = evaluate(y[mask], scores[name][mask])
    metrics = {
        "nested_selection_oof": nested_metrics,
        "selected_candidate_oof_exploratory": selected_metrics,
        "selected_candidate": {"feature_set": str(winner.feature_set),
                               "treatment": str(winner.treatment)},
    }
    (OUTPUT / "metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
    manifest = {
        "cutoff": CUTOFF, "users": len(core), "churners": int(y.sum()),
        "feature_engineering": {
            "source_aggregate_features": aggregate,
            "engineered_features": [col for col in engineered if col not in aggregate],
            "uses_only_pre_cutoff_features": True,
        },
        "candidate_feature_sets": list(FEATURE_SETS),
        "candidate_treatments": list(TREATMENTS),
        "feature_selection": "For SHAP15, CatBoost SHAP ranking is fit on each training fold only.",
        "imputation": "Median fitted inside each training fold for all candidates.",
        "smote": "Standardize on training fold, SMOTE to parity, inverse-transform synthetic rows; validation untouched.",
        "selection": "Highest 5-fold candidate AP, F1@20 as tie-breaker; nested 5x3 CV audits the selection procedure.",
        "selected_candidate": metrics["selected_candidate"],
        "selected_features": selected_columns,
        "selected_feature_medians": dict(zip(selected_columns, map(float, final_imputer.statistics_))),
        "model_params": MODEL_PARAMS,
        "limitations": [
            "Single cutoff only; no forward-time validation or independent holdout.",
            "Full-data candidate CV metrics are optimistic after selecting the maximum; use nested-selection OOF for the selection procedure.",
            "Nested-selection OOF may use different configurations per outer fold, unlike the saved final model.",
            "SHAP magnitudes are model dependence, not causal effects.",
            "Scores are not probability-calibrated.",
        ],
    }
    (OUTPUT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({
        "selected": name,
        "nested_ap": nested_metrics["all_core"]["pr_auc_ap"],
        "nested_f1_20": nested_metrics["all_core"]["top_20pct"]["f1"],
        "candidate_ap": selected_metrics["all_core"]["pr_auc_ap"],
        "candidate_f1_20": selected_metrics["all_core"]["top_20pct"]["f1"],
        "output": str(OUTPUT),
    }, indent=2), flush=True)


if __name__ == "__main__":
    if len(sys.argv) == 2 and sys.argv[1] == "--refresh-selected-shap":
        refresh_selected_model_shap()
    else:
        main()
