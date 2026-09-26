"""Fair 5-fold class-imbalance comparison on the core cohort.

All treatments share the same users, folds, features, median imputation,
CatBoost parameters, and untouched validation folds. ROS/SMOTE touch only
each training fold. Outputs JSON plus a presentation-ready PNG table.
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib import font_manager
import numpy as np
import pandas as pd
from catboost import CatBoostClassifier
from imblearn.over_sampling import RandomOverSampler, SMOTE
from sklearn.impute import SimpleImputer
from sklearn.model_selection import StratifiedKFold

from modeling.train_core_churn import CUTOFF, EXCLUDE, FOLDS, MODEL_PARAMS, SEED, evaluate, load_core


OUTPUT = Path(__file__).resolve().parents[1] / f"models/core_imbalance_{CUTOFF}"
TREATMENTS = ("none", "class_weight_2", "class_weight_balanced", "ros", "smote")
DISPLAY = {
    "none": "무처리",
    "class_weight_2": "클래스 가중치 2",
    "class_weight_balanced": "클래스 균형 가중치",
    "ros": "ROS (단순 복제)",
    "smote": "SMOTE (합성 표본)",
}


def _font():
    for name in ("Malgun Gothic", "맑은 고딕", "NanumGothic", "Noto Sans CJK KR"):
        if any(font.name == name for font in font_manager.fontManager.ttflist):
            return name
    return "DejaVu Sans"


def fit_predict(x_train, y_train, x_val, treatment):
    """Resample only inside the training fold; validation is never modified."""
    imputer = SimpleImputer(strategy="median")
    train = imputer.fit_transform(x_train)
    validation = imputer.transform(x_val)
    params = MODEL_PARAMS.copy()
    if treatment == "class_weight_2":
        params["class_weights"] = [1.0, 2.0]
    elif treatment == "class_weight_balanced":
        positive_weight = float((y_train == 0).sum() / (y_train == 1).sum())
        params["class_weights"] = [1.0, positive_weight]
    elif treatment == "ros":
        train, y_train = RandomOverSampler(random_state=SEED).fit_resample(train, y_train)
    elif treatment == "smote":
        train, y_train = SMOTE(random_state=SEED, k_neighbors=5).fit_resample(train, y_train)
    elif treatment != "none":
        raise ValueError(treatment)
    model = CatBoostClassifier(**params)
    model.fit(train, y_train)
    return model.predict_proba(validation)[:, 1]


def _pct(value):
    return f"{value * 100:.1f}%"


def make_table(metrics, path):
    plt.rcParams["font.family"] = _font()
    fig, ax = plt.subplots(figsize=(15, 6.8), dpi=180)
    fig.patch.set_facecolor("#ffffff")
    ax.axis("off")
    fig.text(0.05, 0.94, "진성 활동 고객 이탈 예측 — 불균형 처리 비교", fontsize=20,
             fontweight="bold", color="#152536")
    fig.text(0.05, 0.895, "동일한 2,381명 · 동일한 5-fold · 같은 CatBoost · 검증 fold 원래 분포 유지",
             fontsize=11, color="#52616e")
    headers = ["학습 처리", "PR-AUC", "ROC-AUC", "상위 10%\nRecall / Precision / F1",
               "상위 20%\nRecall / Precision / F1", "20% 발견 / 오탐"]
    rows = []
    for name in TREATMENTS:
        values = metrics[name]["all_core"]
        top10, top20 = values["top_10pct"], values["top_20pct"]
        rows.append([
            DISPLAY[name], f'{values["pr_auc_ap"]:.3f}', f'{values["roc_auc"]:.3f}',
            f'{_pct(top10["recall"])} / {_pct(top10["precision"])} / {top10["f1"]:.3f}',
            f'{_pct(top20["recall"])} / {_pct(top20["precision"])} / {top20["f1"]:.3f}',
            f'{top20["found_churn"]}명 / {top20["false_alarms"]}명',
        ])
    table = ax.table(cellText=rows, colLabels=headers, cellLoc="center", colLoc="center",
                     colWidths=[.19, .10, .10, .22, .22, .17], bbox=[.05, .26, .90, .60])
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    best_budget = max(TREATMENTS, key=lambda key: metrics[key]["all_core"]["top_20pct"]["f1"])
    for (row, col), cell in table.get_celld().items():
        cell.set_linewidth(0)
        if row == 0:
            cell.set_facecolor("#14334a")
            cell.get_text().set_color("#ffffff")
            cell.get_text().set_fontweight("bold")
        else:
            name = TREATMENTS[row - 1]
            cell.set_facecolor("#e9f4f2" if name == best_budget else ("#f4f7fa" if row % 2 == 0 else "#ffffff"))
            cell.get_text().set_color("#173042")
            if col == 0:
                cell.get_text().set_ha("left")
    fig.text(0.05, 0.18, "상위 10%: 239명 · 상위 20%: 477명 · 실제 중단자: 363명 (15.25%)",
             fontsize=10.5, color="#243e52")
    fig.text(0.05, 0.13, "연두 행: 상위 20% F1 최고. PR-AUC는 전체 순위 품질, 나머지는 조치 규모별 성능입니다.",
             fontsize=10, color="#52616e")
    fig.text(0.05, 0.085, "한 기준일의 교차검증입니다. 새 날짜 검증·확률 보정·캠페인 효과 검증 전에는 운영 성능으로 해석할 수 없습니다.",
             fontsize=9.5, color="#52616e")
    fig.savefig(path, dpi=180, facecolor=fig.get_facecolor(), bbox_inches="tight")
    plt.close(fig)


def main():
    core = load_core()
    columns = [column for column in core.columns if column not in EXCLUDE
               and column not in {"churn", "play_style", "activity_trend"}]
    x = core[columns]
    y = core.churn.to_numpy(dtype=int)
    groups = np.where(core.play_style.eq("ranked_solo_focused"), "solo_focused", "other")
    splits = list(StratifiedKFold(n_splits=FOLDS, shuffle=True,
                                  random_state=SEED).split(x, y))
    results = {}
    for treatment in TREATMENTS:
        scores = np.full(len(core), np.nan)
        for fold, (train_idx, val_idx) in enumerate(splits, start=1):
            scores[val_idx] = fit_predict(x.iloc[train_idx], y[train_idx],
                                          x.iloc[val_idx], treatment)
            print(f"{treatment}: fold {fold}/{FOLDS}", flush=True)
        if not np.isfinite(scores).all():
            raise ValueError(f"Incomplete OOF scores for {treatment}")
        results[treatment] = {"all_core": evaluate(y, scores)}
        for group in ("solo_focused", "other"):
            mask = groups == group
            results[treatment][group] = evaluate(y[mask], scores[mask])
    OUTPUT.mkdir(parents=True, exist_ok=True)
    (OUTPUT / "metrics.json").write_text(json.dumps(results, ensure_ascii=False, indent=2),
                                           encoding="utf-8")
    (OUTPUT / "method.json").write_text(json.dumps({
        "source": "core_ml_features/core_targets from core_segments_2026-08-01.db",
        "users": len(core), "churners": int(y.sum()), "folds": FOLDS, "seed": SEED,
        "model_params": MODEL_PARAMS, "features": columns,
        "treatments": list(TREATMENTS),
        "imputation": "training-fold median for all methods; applied to validation fold without refitting",
        "resampling": "ROS/SMOTE on training fold only, minority to parity",
        "warning": "Single cutoff, same-fold exploratory comparison; no external-date validation",
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    make_table(results, OUTPUT / "comparison_table.png")
    print("Saved:", OUTPUT)
    for name in TREATMENTS:
        values = results[name]["all_core"]
        print(name, "AP", round(values["pr_auc_ap"], 4),
              "Recall@20", round(values["top_20pct"]["recall"], 4),
              "F1@20", round(values["top_20pct"]["f1"], 4))


if __name__ == "__main__":
    main()
