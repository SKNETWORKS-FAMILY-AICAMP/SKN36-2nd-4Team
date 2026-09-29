import json
from pathlib import Path

from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.get("/eda/position-monthly")
def read_position_monthly() -> dict:
    path = Path(__file__).resolve().parents[2] / "data" / "core_dashboard.json"
    if not path.is_file():
        raise HTTPException(status_code=503, detail="로컬 분석 데이터가 준비되지 않았습니다.")
    payload = json.loads(path.read_text(encoding="utf-8"))
    return {"mode": "RANKED_SOLO", "months_available": sorted({row["month"] for row in payload.get("monthly_position", [])}), "items": payload.get("monthly_position", [])}
