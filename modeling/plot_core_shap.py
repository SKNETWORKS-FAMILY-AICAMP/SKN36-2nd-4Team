"""Export the selected 2,381-user CatBoost SHAP ranking as a PNG.

Run from the project root: python -m modeling.plot_core_shap
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib import font_manager


ROOT = Path(__file__).resolve().parents[1]
MODEL_DIR = ROOT / "models/core_reselected_2026-08-01"
SOURCE = MODEL_DIR / "selected_model_shap_importance.csv"
DEFAULT_OUTPUT = MODEL_DIR / "shap_core_2381_top15.png"

LABELS = {
    "days_since_last_game": "마지막 경기 경과일",
    "games_7d": "최근 7일 경기 수",
    "active_days_30d": "최근 30일 활동일",
    "mode_switch_rate_20": "최근 20경기 모드 전환율",
    "winrate_change_10": "최근 승률 변화",
    "last_gap": "마지막 경기 간격",
    "avg_cs_per_min_20": "최근 평균 분당 CS",
    "max_gap_30d": "최근 최대 경기 간격",
    "avg_vision_per_min_20": "최근 평균 분당 시야 점수",
    "avg_kda_20": "최근 평균 KDA",
    "unique_modes_30d": "최근 30일 이용 모드 수",
    "games_30d": "최근 30일 경기 수",
    "games_prev30d": "이전 30일 경기 수",
    "winrate_20": "최근 20경기 승률",
    "games_90d": "최근 90일 경기 수",
}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--top", type=int, default=15, help="Number of features to show")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    if not 1 <= args.top <= 33:
        parser.error("--top must be between 1 and 33")

    with SOURCE.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))[: args.top]
    if not rows:
        raise ValueError(f"No SHAP values in {SOURCE}")

    fonts = {font.name for font in font_manager.fontManager.ttflist}
    if "Malgun Gothic" in fonts:
        plt.rcParams["font.family"] = "Malgun Gothic"
    plt.rcParams["axes.unicode_minus"] = False

    names = [LABELS.get(row["feature"], row["feature"]) for row in rows][::-1]
    values = [float(row["mean_abs_shap"]) for row in rows][::-1]
    fig, ax = plt.subplots(figsize=(10, 7.2), facecolor="white")
    ax.set_facecolor("white")
    bars = ax.barh(names, values, color="#3673b5", height=0.7)
    ax.set_xlim(0, max(values) * 1.2)
    ax.set_xlabel("평균 |SHAP|  ·  모델 출력 로그오즈 기준", color="#323b47", labelpad=12)
    ax.xaxis.grid(True, color="#e5e9ef", linewidth=0.8)
    ax.set_axisbelow(True)
    ax.tick_params(axis="both", length=0, labelcolor="#263442", pad=8)
    for spine in ax.spines.values():
        spine.set_visible(False)
    for bar, value in zip(bars, values):
        ax.text(value + max(values) * 0.012,
                bar.get_y() + bar.get_height() / 2,
                f"{value:.3f}", va="center", fontsize=9, color="#263442")
    fig.suptitle("진성 활동 고객 CatBoost · SHAP 중요도", x=0.08, y=0.98,
                 ha="left", fontsize=17, fontweight="bold", color="#111d2b")
    fig.text(0.08, 0.895,
             "진성 고객 2,381명 · 선택 후보: 기존 33개 변수 + 클래스 균형 가중치",
             ha="left", fontsize=10, color="#526171")
    fig.text(0.08, 0.045,
             "막대는 예측에 대한 평균 기여 크기입니다. 영향 방향·이탈 원인·보상 효과는 보여주지 않습니다.",
             ha="left", fontsize=9, color="#526171")
    fig.subplots_adjust(left=0.32, right=0.92, top=0.83, bottom=0.14)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.output, dpi=240, facecolor="white")
    plt.close(fig)
    print(args.output)


if __name__ == "__main__":
    main()
