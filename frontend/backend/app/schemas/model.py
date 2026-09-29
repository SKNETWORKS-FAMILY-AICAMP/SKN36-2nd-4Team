from typing import Any

from pydantic import BaseModel

from app.schemas.common import ModelStatus


class ModelMetricsResponse(BaseModel):
    """모델 평가 지표 응답."""

    model_status: ModelStatus
    model_version: str | None
    metrics: dict[str, float]
    message: str | None = None
    details: dict[str, Any] | None = None
