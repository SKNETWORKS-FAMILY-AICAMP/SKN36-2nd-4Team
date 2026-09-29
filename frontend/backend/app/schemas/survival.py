from pydantic import BaseModel, Field


class SyntheticSurvivalUser(BaseModel):
    """One synthetic Cox test-split prediction; not an operational estimate."""

    record_id: str
    player_id: str
    risk_band: str
    risk_rank: int = Field(ge=1)
    event_risk_7d: float = Field(ge=0, le=1)
    event_risk_14d: float = Field(ge=0, le=1)
    event_risk_30d: float = Field(ge=0, le=1)
    activity_survival_7d: float = Field(ge=0, le=1)
    activity_survival_14d: float = Field(ge=0, le=1)
    activity_survival_30d: float = Field(ge=0, le=1)


class SyntheticSurvivalResponse(BaseModel):
    demo: bool = True
    cutoff_date: str
    cohort_users: int
    test_users: int
    c_index: float = Field(ge=0, le=1)
    risk_band_definition: str
    warning: str
    items: list[SyntheticSurvivalUser]
