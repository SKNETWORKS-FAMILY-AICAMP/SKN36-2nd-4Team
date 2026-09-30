from fastapi import APIRouter, HTTPException

from app.services.dashboard_store import get_dashboard_payload

router = APIRouter()


@router.get("/eda/position-monthly")
def read_position_monthly() -> dict:
    payload = get_dashboard_payload()
    if not payload:
        raise HTTPException(status_code=503, detail="로컬 분석 데이터가 준비되지 않았습니다.")
    return {"mode": "RANKED_SOLO", "months_available": sorted({row["month"] for row in payload.get("monthly_position", [])}), "items": payload.get("monthly_position", [])}
