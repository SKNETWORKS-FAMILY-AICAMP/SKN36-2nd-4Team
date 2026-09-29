from fastapi import APIRouter

from app.schemas.model import ModelMetricsResponse


router = APIRouter()


@router.get("/model/metrics", response_model=ModelMetricsResponse)
def read_model_metrics() -> ModelMetricsResponse:
    """모델 평가 결과가 준비되기 전의 상태를 반환한다."""
    return ModelMetricsResponse(
        model_status="pending",
        model_version=None,
        metrics={},
        message="모델 담당자의 평가 결과를 기다리고 있습니다.",
    )

