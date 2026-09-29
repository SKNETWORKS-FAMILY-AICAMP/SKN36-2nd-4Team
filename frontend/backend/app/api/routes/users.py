from fastapi import APIRouter, HTTPException, Query, status

from app.schemas.user import RiskUser, UserDetailResponse
from app.services.user_service import get_user_detail, search_users


router = APIRouter()


@router.get("/users/search", response_model=list[RiskUser])
def search_user_candidates(
    q: str = Query(min_length=1),
    limit: int = Query(default=8, ge=1, le=20),
) -> list[RiskUser]:
    """분석용 player_id / 조합 키 검색 결과를 반환한다."""
    return search_users(query=q, limit=limit)


@router.get("/users/{record_id}", response_model=UserDetailResponse)
def read_user(record_id: str) -> UserDetailResponse:
    """기준일 이전 경기 이력과 모델 점수를 반환한다."""
    detail = get_user_detail(record_id)
    if detail is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자를 찾을 수 없습니다.",
        )
    return detail
