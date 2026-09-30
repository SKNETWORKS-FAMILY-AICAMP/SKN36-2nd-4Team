from pydantic import BaseModel, Field

from app.schemas.common import ModelStatus


class RiskUser(BaseModel):
    """위험 사용자 목록의 한 행."""

    record_id: str
    player_id: str
    risk_score: float = Field(ge=0, le=1)
    risk_level: str
    last_game_days: int = Field(ge=0)
    recent_matches: int = Field(ge=0)
    win_rate: float = Field(ge=0, le=1)
    main_reason: str
    rank: int = Field(default=0, ge=0)


class RiskOverview(BaseModel):
    total_users: int
    high_risk_users: int
    average_score: float = Field(ge=0, le=1)
    campaign_target_users: int
    average_inactive_days: float = Field(ge=0)


class RiskDistributionPoint(BaseModel):
    label: str
    count: int


class RiskUserListResponse(BaseModel):
    """페이지 나누기가 적용된 위험 사용자 목록."""

    items: list[RiskUser]
    page: int
    size: int
    total: int
    matched: int = 0
    model_status: ModelStatus
    demo: bool = True
    overview: RiskOverview
    distribution: list[RiskDistributionPoint]
    message: str | None = None


class ActivityPoint(BaseModel):
    date: str
    matches: int = Field(ge=0)


class PerformancePoint(BaseModel):
    match_no: int
    kda: float = Field(ge=0)
    win: int = Field(ge=0, le=1)
    damage: int = Field(ge=0)
    cs: int = Field(ge=0)
    vision: int = Field(ge=0)
    duration_minutes: int = Field(ge=0)


class IntervalPoint(BaseModel):
    label: str
    days: float = Field(ge=0)


class ModePoint(BaseModel):
    mode: str
    count: int = Field(ge=0)


class RiskReason(BaseModel):
    feature: str
    label: str
    contribution: float
    direction: str


class UserDetailResponse(BaseModel):
    record_id: str
    player_id: str
    risk_score: float = Field(ge=0, le=1)
    risk_level: str
    last_game_days: int = Field(ge=0)
    recent_matches: int = Field(ge=0)
    recent_win_rate: float = Field(ge=0, le=1)
    average_kda: float = Field(ge=0)
    average_interval_days: float = Field(ge=0)
    model_status: ModelStatus
    demo: bool = True
    activity: list[ActivityPoint]
    performance: list[PerformancePoint]
    intervals: list[IntervalPoint]
    modes: list[ModePoint]
    reasons: list[RiskReason]
