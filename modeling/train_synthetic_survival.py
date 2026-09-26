"""Synthetic survival-analysis demo for the established active cohort.

This script does not create new real labels. It uses the audited core cohort as
the population shape, then simulates a longer observation window so we can show
how survival models answer "when should we intervene?".
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib import font_manager
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

try:
    from lifelines import CoxPHFitter, KaplanMeierFitter
    from lifelines.utils import concordance_index
except ImportError as exc:  # pragma: no cover - user-facing environment guard
    raise SystemExit(
        "lifelines is required. Run: .\\.venv\\Scripts\\python.exe -m pip install -r requirements.txt"
    ) from exc

from modeling.train_core_churn import CUTOFF, load_core


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / f"models/synthetic_survival_{CUTOFF}"
DERIVED = ROOT / "lol_churn_all_data" / "derived"
DATASET = DERIVED / f"synthetic_survival_core_{CUTOFF}.csv"
SEED = 42
HORIZONS = (7, 14, 30, 60, 90)

ID_COLUMNS = ["team_id", "player_id", "cutoff_date"]
NUMERIC_FEATURES = [
    "games_7d",
    "games_30d",
    "games_prev30d",
    "activity_change_30d",
    "active_days_30d",
    "days_since_last_game",
    "avg_gap_30d",
    "max_gap_30d",
    "last_gap",
    "winrate_20",
    "avg_kda_20",
    "avg_deaths_20",
    "losing_streak",
    "winrate_change_10",
    "unique_champions_20",
    "mode_switch_rate_20",
    "ranked_solo_ratio_30d",
    "ranked_flex_ratio_30d",
    "normal_ratio_30d",
    "aram_ratio_30d",
]
CATEGORICAL_FEATURES = ["play_style", "activity_trend"]


def _font() -> str:
    for name in ("Malgun Gothic", "맑은 고딕", "NanumGothic", "Noto Sans CJK KR"):
        if any(font.name == name for font in font_manager.fontManager.ttflist):
            return name
    return "DejaVu Sans"


def _zscore(series: pd.Series) -> pd.Series:
    values = series.astype(float)
    std = values.std(ddof=0)
    if not np.isfinite(std) or std == 0:
        return values * 0.0
    return (values - values.mean()) / std


def synthetic_linear_risk(core: pd.DataFrame) -> pd.Series:
    """Transparent assumptions for synthetic time-to-inactivity risk."""
    values = core.copy()
    values[NUMERIC_FEATURES] = values[NUMERIC_FEATURES].replace([np.inf, -np.inf], np.nan)
    values[NUMERIC_FEATURES] = values[NUMERIC_FEATURES].fillna(values[NUMERIC_FEATURES].median())
    risk = (
        0.70 * values["churn"].astype(float)
        + 0.45 * _zscore(values["days_since_last_game"])
        + 0.35 * _zscore(values["avg_gap_30d"])
        - 0.30 * _zscore(values["games_30d"])
        - 0.20 * _zscore(values["active_days_30d"])
        + 0.22 * values["activity_trend"].eq("activity_declining").astype(float)
        - 0.12 * values["activity_trend"].eq("activity_growing").astype(float)
        + 0.15 * _zscore(values["losing_streak"])
        + 0.10 * _zscore(values["avg_deaths_20"])
        - 0.10 * _zscore(values["avg_kda_20"])
        - 0.08 * _zscore(values["winrate_change_10"])
    )
    return risk.clip(-2.5, 2.5)


def calibrate_base_hazard(risk: pd.Series, random_uniform: np.ndarray, target_rate: float) -> float:
    """Choose a baseline so synthetic events by 30 days match core churn rate."""
    low, high = 0.0001, 1.0
    exp_risk = np.exp(risk.to_numpy())
    for _ in range(60):
        mid = (low + high) / 2
        duration = -np.log(random_uniform) / (mid * exp_risk)
        if np.mean(duration <= 30) < target_rate:
            low = mid
        else:
            high = mid
    return (low + high) / 2


def build_synthetic_dataset(core: pd.DataFrame) -> pd.DataFrame:
    rng = np.random.default_rng(SEED)
    risk = synthetic_linear_risk(core)
    event_uniform = rng.uniform(0.001, 0.999, size=len(core))
    target_30d = float(core["churn"].mean())
    base_hazard = calibrate_base_hazard(risk, event_uniform, target_30d)
    raw_duration = -np.log(event_uniform) / (base_hazard * np.exp(risk.to_numpy()))

    censor_days = rng.uniform(75, 180, size=len(core))
    duration = np.minimum(raw_duration, censor_days)
    event_observed = raw_duration <= censor_days

    result = core[ID_COLUMNS + NUMERIC_FEATURES + CATEGORICAL_FEATURES + ["churn"]].copy()
    result["synthetic_duration_days"] = np.round(duration, 2)
    result["synthetic_event_observed"] = event_observed.astype(int)
    result["synthetic_event_by_30d"] = (raw_duration <= 30).astype(int)
    result["synthetic_risk_driver"] = np.round(risk, 6)
    result["synthetic_note"] = "demo_only_not_real_observation"
    result.attrs["base_hazard"] = base_hazard
    return result


def design_matrix(frame: pd.DataFrame) -> pd.DataFrame:
    values = frame[NUMERIC_FEATURES + CATEGORICAL_FEATURES].copy()
    values[NUMERIC_FEATURES] = values[NUMERIC_FEATURES].replace([np.inf, -np.inf], np.nan)
    values[NUMERIC_FEATURES] = values[NUMERIC_FEATURES].fillna(values[NUMERIC_FEATURES].median())
    values = pd.get_dummies(values, columns=CATEGORICAL_FEATURES, drop_first=True, dtype=float)
    scaled = values.copy()
    scaler = StandardScaler()
    scaled[NUMERIC_FEATURES] = scaler.fit_transform(scaled[NUMERIC_FEATURES])
    scaled["synthetic_duration_days"] = frame["synthetic_duration_days"].to_numpy()
    scaled["synthetic_event_observed"] = frame["synthetic_event_observed"].to_numpy(dtype=int)
    return scaled


def evaluate_survival(model: CoxPHFitter, test_x: pd.DataFrame) -> dict:
    partial_hazard = model.predict_partial_hazard(test_x)
    cindex = concordance_index(
        test_x["synthetic_duration_days"],
        -partial_hazard.to_numpy().ravel(),
        test_x["synthetic_event_observed"],
    )
    survival = model.predict_survival_function(
        test_x.drop(columns=["synthetic_duration_days", "synthetic_event_observed"]),
        times=list(HORIZONS),
    ).T
    survival.columns = [f"survival_{day}d" for day in HORIZONS]
    return {"concordance_index": float(cindex)}, survival


def save_curves(model: CoxPHFitter, test_x: pd.DataFrame, synthetic: pd.DataFrame, path: Path) -> None:
    plt.rcParams["font.family"] = _font()
    fig, ax = plt.subplots(figsize=(12, 7), dpi=170)
    fig.patch.set_facecolor("#ffffff")
    ax.set_facecolor("#ffffff")

    kmf = KaplanMeierFitter()
    kmf.fit(
        synthetic["synthetic_duration_days"],
        synthetic["synthetic_event_observed"],
        label="합성 전체 cohort",
    )
    kmf.plot_survival_function(ax=ax, color="#355C7D", linewidth=2.6, ci_show=False)

    feature_only = test_x.drop(columns=["synthetic_duration_days", "synthetic_event_observed"])
    hazards = model.predict_partial_hazard(feature_only).to_numpy().ravel()
    low_row = feature_only.iloc[[np.argmin(hazards)]]
    high_row = feature_only.iloc[[np.argmax(hazards)]]
    model.predict_survival_function(low_row, times=np.arange(1, 121)).plot(
        ax=ax, color="#2A9D8F", linewidth=2.4, label="낮은 위험 예시"
    )
    model.predict_survival_function(high_row, times=np.arange(1, 121)).plot(
        ax=ax, color="#E76F51", linewidth=2.4, label="높은 위험 예시"
    )

    ax.set_title("Synthetic Survival Demo: 경기 중단 위험 시점", fontsize=18, fontweight="bold", pad=14)
    ax.set_xlabel("기준일 이후 경과일")
    ax.set_ylabel("아직 30일 무경기 상태에 도달하지 않았을 확률")
    ax.set_xlim(0, 120)
    ax.set_ylim(0, 1.02)
    ax.grid(True, axis="y", color="#dde3ea", linewidth=0.8)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(loc="upper right", frameon=False)
    fig.text(
        0.08,
        0.03,
        "주의: 실제 관찰 기간이 아니라 진성고객 feature 분포로 만든 합성 생존분석 예시입니다.",
        fontsize=10,
        color="#52616e",
    )
    fig.savefig(path, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)


def write_report(metrics: dict, summary: dict, coefficients: pd.DataFrame) -> None:
    top_coef = coefficients.reindex(coefficients["coef"].abs().sort_values(ascending=False).index).head(8)
    coef_rows = "\n".join(
        f"| `{row.covariate}` | {row.coef:.3f} | {row.hazard_ratio:.2f} |"
        for row in top_coef.itertuples()
    )
    report = f"""# Synthetic Survival Model Demo

이 폴더의 결과는 실제 장기 관찰 정답이 아니라, 진성 활동 고객 {summary["users"]:,}명의 feature 분포를 바탕으로 만든 **합성 생존분석 데모**입니다.

## 목적

- CatBoost: 기준일 이후 30일 이탈 위험 고객을 고르는 모델
- Synthetic survival model: 위험 고객에게 **언제 개입할지**를 설명하는 발표용 확장 실험

## 합성 데이터 정의

| 항목 | 값 |
|---|---:|
| 기준일 | {CUTOFF} |
| 합성 사용자 수 | {summary["users"]:,} |
| 실제 core churn 비율 | {summary["real_churn_rate"]:.1%} |
| 합성 30일 event 비율 | {summary["synthetic_event_30d_rate"]:.1%} |
| 합성 관찰 event 비율 | {summary["synthetic_event_observed_rate"]:.1%} |
| 합성 관찰 최대일 | {summary["max_duration_days"]:.1f} |

합성 event는 `30일 무경기 상태에 도달`로 해석했습니다. 실제 경기 로그에서 확인한 값이 아니라 `days_since_last_game`, `avg_gap_30d`, `games_30d`, `activity_trend`, `losing_streak`, KDA 등으로 위험도를 만든 뒤 시뮬레이션했습니다.

## 모델 결과

| 모델 | 평가 |
|---|---:|
| Cox Proportional Hazards | Concordance index {metrics["concordance_index"]:.3f} |

Concordance index는 생존분석의 순위 지표입니다. 1에 가까울수록 더 이른 event가 발생한 사용자를 더 위험하게 정렬했다는 뜻입니다.

## 영향이 큰 합성 요인

| 변수 | Cox 계수 | Hazard ratio |
|---|---:|---:|
{coef_rows}

## 사용 방법

- `synthetic_survival_core_{CUTOFF}.csv`: 합성 생존분석 학습 데이터
- `survival_predictions.csv`: 테스트 사용자별 7/14/30/60/90일 생존확률
- `survival_curves.png`: 발표용 생존곡선 이미지
- `cox_coefficients.csv`: Cox 계수와 hazard ratio

## 한계

이 결과는 CatBoost 실제 이탈 예측 성능과 비교하면 안 됩니다. 실제 장기 관찰 로그가 없어서 event time과 censoring을 인위적으로 만들었기 때문입니다. 보고서에서는 `생존분석을 적용하면 어떤 질문에 답할 수 있는지`를 보여주는 데 사용하세요.
"""
    (OUTPUT / "RESULTS.md").write_text(report, encoding="utf-8")


def main() -> None:
    core = load_core()
    synthetic = build_synthetic_dataset(core)
    DERIVED.mkdir(parents=True, exist_ok=True)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    synthetic.to_csv(DATASET, index=False, encoding="utf-8-sig")

    matrix = design_matrix(synthetic)
    train_x, test_x = train_test_split(
        matrix,
        test_size=0.3,
        random_state=SEED,
        stratify=matrix["synthetic_event_observed"],
    )
    model = CoxPHFitter(penalizer=0.05)
    model.fit(train_x, duration_col="synthetic_duration_days", event_col="synthetic_event_observed")

    metrics, survival = evaluate_survival(model, test_x)
    predictions = synthetic.loc[test_x.index, ID_COLUMNS + ["churn", "synthetic_duration_days", "synthetic_event_observed"]].copy()
    predictions = pd.concat([predictions.reset_index(drop=True), survival.reset_index(drop=True)], axis=1)
    predictions.to_csv(OUTPUT / "survival_predictions.csv", index=False, encoding="utf-8-sig")

    coefficients = model.summary.reset_index()[["covariate", "coef", "exp(coef)", "p"]]
    coefficients = coefficients.rename(columns={"exp(coef)": "hazard_ratio", "p": "p_value"})
    coefficients.to_csv(OUTPUT / "cox_coefficients.csv", index=False, encoding="utf-8-sig")

    save_curves(model, test_x, synthetic, OUTPUT / "survival_curves.png")
    summary = {
        "users": int(len(synthetic)),
        "real_churn_rate": float(synthetic["churn"].mean()),
        "synthetic_event_30d_rate": float(synthetic["synthetic_event_by_30d"].mean()),
        "synthetic_event_observed_rate": float(synthetic["synthetic_event_observed"].mean()),
        "max_duration_days": float(synthetic["synthetic_duration_days"].max()),
        "base_hazard": float(synthetic.attrs["base_hazard"]),
        "seed": SEED,
        "horizons": list(HORIZONS),
        "warning": "Synthetic demonstration only; not a real observed survival label.",
    }
    (OUTPUT / "metrics.json").write_text(
        json.dumps({"summary": summary, "metrics": metrics}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    write_report(metrics, summary, coefficients)
    print(json.dumps({"output": str(OUTPUT), "dataset": str(DATASET), **metrics, **summary}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
