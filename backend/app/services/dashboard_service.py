from fastapi import HTTPException

from app.schemas.summary import ChurnRatePoint, SummaryKpis, SummaryResponse
from app.services.dashboard_store import get_dashboard_payload


def _mode_summary(game_mode: str) -> tuple[dict, int]:
    payload = get_dashboard_payload()
    if not payload:
        raise HTTPException(status_code=503, detail="로컬 분석 데이터가 준비되지 않았습니다.")
    stats = payload.get("mode_summary", {}).get(game_mode)
    if not stats:
        stats = payload.get("mode_summary", {}).get("ALL", {"users": 2381, "churners": 363})
    total_collected = int(payload.get("total_collected_users", 9879))
    return stats, total_collected


def get_dashboard_summary(game_mode: str = "ALL") -> SummaryResponse:
    """진성 활동 고객 배치의 운영 요약값을 반환한다."""
    mode_stats, total_collected = _mode_summary(game_mode)
    users, churners = int(mode_stats["users"]), int(mode_stats["churners"])
    rate = churners / users if users else 0.0

    return SummaryResponse(
        cutoff_date="2026-08-01",
        collection_scope=f"전체 수집 사용자 {total_collected:,}명",
        model_status="ready",
        kpis=SummaryKpis(
            total_users=total_collected,
            model_eligible_users=users,
            actual_churn_users=churners,
            actual_churn_rate=rate,
            unique_matches=int(mode_stats.get("match_records", 0)),
        ),
        inactivity_churn_rates=[ChurnRatePoint(**point) for point in mode_stats.get("inactivity_churn_rates", [])],
        activity_churn_rates=[ChurnRatePoint(**point) for point in mode_stats.get("activity_churn_rates", [])],
        data_quality_notes=[
            f"현재 필터: {game_mode}. 모드 비율이 0인 사용자는 해당 모드 집계에서 제외합니다.",
            "churn은 기준일 이후 30일 동안 경기 기록이 없는 상태입니다.",
        ],
    )
