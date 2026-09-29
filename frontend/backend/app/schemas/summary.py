from pydantic import BaseModel, Field

from app.schemas.common import ModelStatus


class SummaryKpis(BaseModel):
    """전체 현황 상단 카드에 표시할 핵심 수치."""

    total_users: int = Field(ge=0)
    model_eligible_users: int = Field(ge=0)
    actual_churn_users: int = Field(ge=0)
    actual_churn_rate: float = Field(ge=0, le=1)
    unique_matches: int = Field(ge=0)


class ChurnRatePoint(BaseModel):
    """구간별 실제 이탈률 그래프의 한 점."""

    label: str
    rate: float = Field(ge=0, le=1)


class SummaryResponse(BaseModel):
    """전체 현황 페이지의 전체 응답 구조."""

    cutoff_date: str
    collection_scope: str
    model_status: ModelStatus
    kpis: SummaryKpis
    inactivity_churn_rates: list[ChurnRatePoint]
    activity_churn_rates: list[ChurnRatePoint]
    data_quality_notes: list[str]

