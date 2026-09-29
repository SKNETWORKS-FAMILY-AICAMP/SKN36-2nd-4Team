import csv
from pathlib import Path

from fastapi import APIRouter, HTTPException

from app.schemas.survival import SyntheticSurvivalResponse, SyntheticSurvivalUser


router = APIRouter()
PREDICTIONS_PATH = (
    Path(__file__).resolve().parents[4]
    / "models"
    / "synthetic_survival_2026-08-01"
    / "survival_predictions.csv"
)


@router.get("/survival/synthetic-users", response_model=SyntheticSurvivalResponse)
def read_synthetic_survival_users() -> SyntheticSurvivalResponse:
    """Return the precomputed synthetic Cox holdout predictions for the demo."""
    if not PREDICTIONS_PATH.is_file():
        raise HTTPException(
            status_code=503,
            detail="합성 생존분석 예측 파일을 찾을 수 없습니다.",
        )

    with PREDICTIONS_PATH.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))

    rows.sort(key=lambda row: float(row["survival_30d"]))
    high_count = max(1, round(len(rows) * 0.20)) if rows else 0
    watch_count = max(1, round(len(rows) * 0.20)) if rows else 0
    items: list[SyntheticSurvivalUser] = []

    for index, row in enumerate(rows):
        survival_7d = float(row["survival_7d"])
        survival_14d = float(row["survival_14d"])
        survival_30d = float(row["survival_30d"])
        if index < high_count:
            risk_band = "고위험"
        elif index < high_count + watch_count:
            risk_band = "주의"
        else:
            risk_band = "일반 관찰"

        items.append(
            SyntheticSurvivalUser(
                record_id=f"{row['team_id']}:{row['player_id']}",
                player_id=row["player_id"],
                risk_band=risk_band,
                risk_rank=index + 1,
                event_risk_7d=1 - survival_7d,
                event_risk_14d=1 - survival_14d,
                event_risk_30d=1 - survival_30d,
                activity_survival_7d=survival_7d,
                activity_survival_14d=survival_14d,
                activity_survival_30d=survival_30d,
            )
        )

    return SyntheticSurvivalResponse(
        demo=True,
        cutoff_date="2026-08-01",
        cohort_users=2381,
        test_users=len(items),
        c_index=0.762,
        risk_band_definition="합성 시험 표본에서 30일 가상 이벤트 위험 순위 상위 20%는 고위험, 다음 20%는 주의로 구분",
        warning="합성 이벤트 라벨로 산출한 데모입니다. 실제 사용자 이탈 확률이나 운영용 위험 등급이 아닙니다.",
        items=items,
    )
