import json
from pathlib import Path

from fastapi import APIRouter

from app.schemas.model import ModelMetricsResponse


router = APIRouter()


def _model_experiment_path() -> Path:
    return Path(__file__).resolve().parents[2] / "data" / "core_model_experiment.json"


@router.get("/model/metrics", response_model=ModelMetricsResponse)
def read_model_metrics() -> ModelMetricsResponse:
    """커밋된 모델 실험 결과를 모델 성능 페이지에 반환한다.

    이 프로젝트에는 core_model_experiment.json이 이미 포함되어 있으므로
    별도 학습 프로세스가 실행 중이지 않아도 발표/시연 화면은 유지한다.
    """
    path = _model_experiment_path()
    if not path.is_file():
        return ModelMetricsResponse(
            model_status="pending",
            model_version=None,
            metrics={},
            message="모델 평가 스냅샷을 찾지 못했습니다.",
            details=None,
        )

    details = json.loads(path.read_text(encoding="utf-8"))
    nested = details.get("nested_selection_oof", {}).get("all_core", {})
    top20 = nested.get("top_20pct", {})

    metrics = {
        "pr_auc_ap": float(nested.get("pr_auc_ap", 0.0)),
        "roc_auc": float(nested.get("roc_auc", 0.0)),
        "recall_20": float(top20.get("recall", 0.0)),
        "precision_20": float(top20.get("precision", 0.0)),
        "f1_20": float(top20.get("f1", 0.0)),
    }

    return ModelMetricsResponse(
        model_status="ready",
        model_version=details.get("model_version"),
        metrics=metrics,
        message="커밋된 5-Fold OOF 모델 평가 스냅샷입니다.",
        details=details,
    )
