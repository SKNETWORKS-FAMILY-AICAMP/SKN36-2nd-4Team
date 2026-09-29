from fastapi import APIRouter, Query

from app.schemas.summary import SummaryResponse
from app.services.dashboard_service import get_dashboard_summary


router = APIRouter()


@router.get("/summary", response_model=SummaryResponse)
def read_summary(
    game_mode: str = Query(default="ALL"),
) -> SummaryResponse:
    """전체 현황 페이지에 필요한 요약 데이터를 반환한다.

    game_mode 파라미터는 프론트 필터와 실제 데이터 조회를 연결하기 위한 값이다.
    선택한 게임 모드에서 관측된 집계와 이탈률을 반환한다.
    """
    return get_dashboard_summary(game_mode=game_mode)
