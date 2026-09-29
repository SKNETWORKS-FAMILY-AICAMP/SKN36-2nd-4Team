from fastapi import APIRouter, Query

from app.schemas.user import RiskUserListResponse
from app.services.user_service import get_risk_users


router = APIRouter()


@router.get("/risk-users", response_model=RiskUserListResponse)
def read_risk_users(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=100, ge=1, le=5000),
) -> RiskUserListResponse:
    """진성 활동 고객의 CatBoost OOF 점수와 요약 지표를 반환한다."""
    return get_risk_users(page=page, size=size)
