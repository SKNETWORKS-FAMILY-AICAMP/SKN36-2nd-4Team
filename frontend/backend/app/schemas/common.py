from typing import Literal

from pydantic import BaseModel


ModelStatus = Literal["pending", "ready", "error"]


class MetadataResponse(BaseModel):
    """데이터 기준일과 모델 상태 응답."""

    cutoff_date: str
    collection_scope: str
    model_status: ModelStatus
    model_version: str | None

