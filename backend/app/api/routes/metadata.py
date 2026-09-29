from fastapi import APIRouter

from app.schemas.common import MetadataResponse


router = APIRouter()


@router.get("/metadata", response_model=MetadataResponse)
def read_metadata() -> MetadataResponse:
    """데이터와 모델의 현재 버전을 반환한다."""
    return MetadataResponse(
        cutoff_date="2026-08-01",
        collection_scope="Batch 1",
        model_status="pending",
        model_version=None,
    )

