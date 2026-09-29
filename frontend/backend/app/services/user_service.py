import json
from pathlib import Path

from app.schemas.user import (
    ActivityPoint,
    IntervalPoint,
    ModePoint,
    PerformancePoint,
    RiskDistributionPoint,
    RiskOverview,
    RiskUser,
    RiskUserListResponse,
    UserDetailResponse,
)

def _load_dashboard_payload() -> dict:
    path = Path(__file__).resolve().parents[1] / "data" / "core_dashboard.json"
    if not path.exists():
        return {"items": [], "details": {}}
    return json.loads(path.read_text(encoding="utf-8"))


CORE_PAYLOAD = _load_dashboard_payload()
RISK_USERS = [
    RiskUser(**{key: item[key] for key in RiskUser.model_fields})
    for item in CORE_PAYLOAD["items"]
]


def get_risk_users(page: int, size: int) -> RiskUserListResponse:
    start = (page - 1) * size
    end = start + size
    high = [user for user in RISK_USERS if user.risk_level == "HIGH"]
    avg_score = sum(user.risk_score for user in RISK_USERS) / len(RISK_USERS) if RISK_USERS else 0.0
    avg_inactive = sum(user.last_game_days for user in high) / len(high) if high else 0.0
    medium = [user for user in RISK_USERS if user.risk_level == "MEDIUM"]
    low = [user for user in RISK_USERS if user.risk_level == "LOW"]

    return RiskUserListResponse(
        items=RISK_USERS[start:end],
        page=page,
        size=size,
        total=len(RISK_USERS),
        model_status="ready",
        demo=False,
        overview=RiskOverview(
            total_users=len(RISK_USERS),
            high_risk_users=len(high),
            average_score=avg_score,
            campaign_target_users=round(len(RISK_USERS) * 0.2),
            average_inactive_days=round(avg_inactive, 1),
        ),
        distribution=[
            RiskDistributionPoint(label="HIGH", count=len(high)),
            RiskDistributionPoint(label="MEDIUM", count=len(medium)),
            RiskDistributionPoint(label="LOW", count=len(low)),
        ],
        message="진성 활동 고객 2,381명의 CatBoost 5-fold OOF 점수입니다.",
    )


def search_users(query: str, limit: int = 8) -> list[RiskUser]:
    """분석용 player_id 또는 조합 키로 사용자 후보를 검색한다."""
    keyword = query.strip().lower()
    if not keyword:
        return []

    matched = [
        user
        for user in RISK_USERS
        if keyword in user.player_id.lower() or keyword in user.record_id.lower()
    ]
    matched.sort(
        key=lambda user: (
            0 if user.record_id.lower() == keyword or user.player_id.lower() == keyword else 1,
            -user.risk_score,
        )
    )
    return matched[:limit]


def get_user_detail(record_id: str) -> UserDetailResponse | None:
    base = next((user for user in RISK_USERS if user.record_id == record_id), None)
    if base is None:
        return None

    detail = CORE_PAYLOAD.get("details", {}).get(record_id, {})
    events = detail.get("events", [])
    mode_labels = {
        "RANKED_SOLO": "솔로랭크", "RANKED_FLEX": "자유랭크", "NORMAL": "일반 게임",
        "ARAM": "칼바람 나락", "ARENA": "아레나", "OTHER": "기타",
    }
    performance = [
        PerformancePoint(
            match_no=index,
            kda=float(event.get("kda", 0)),
            win=int(event.get("win", 0)),
            damage=int(event.get("damage", 0)),
            cs=int(event.get("cs", 0)),
            vision=int(event.get("vision", 0)),
            duration_minutes=int(event.get("duration_minutes", 0)),
        )
        for index, event in enumerate(events, start=1)
    ]
    intervals = [
        IntervalPoint(label=f"{index}경기 전", days=float(event.get("gap_days", 0)))
        for index, event in enumerate(events, start=1)
    ]
    return UserDetailResponse(
        record_id=base.record_id,
        player_id=base.player_id,
        risk_score=base.risk_score,
        risk_level=base.risk_level,
        last_game_days=base.last_game_days,
        recent_matches=base.recent_matches,
        recent_win_rate=base.win_rate,
        average_kda=float(detail.get("average_kda", 0)),
        average_interval_days=float(detail.get("average_interval_days", 0)),
        model_status="ready",
        demo=False,
        activity=[ActivityPoint(**point) for point in detail.get("activity", [])],
        performance=performance,
        intervals=intervals,
        modes=[ModePoint(mode=mode_labels.get(point["mode"], point["mode"]), count=point["count"]) for point in detail.get("modes", [])],
        reasons=[],
    )
