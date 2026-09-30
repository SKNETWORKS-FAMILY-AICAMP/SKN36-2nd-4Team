from fastapi import APIRouter, Query

from app.schemas.user import RiskUserListResponse
from app.services.user_service import get_risk_users


router = APIRouter()


@router.get("/risk-users", response_model=RiskUserListResponse)
def read_risk_users(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    q: str = Query(default=""),
    risk_level: str | None = Query(default=None),
) -> RiskUserListResponse:
    """진성 활동 고객의 CatBoost OOF 점수와 요약 지표를 반환한다."""
    if risk_level not in {None, "ALL", "HIGH", "MEDIUM", "LOW"}:
        risk_level = None
    return get_risk_users(page=page, size=size, query=q, risk_level=risk_level)
