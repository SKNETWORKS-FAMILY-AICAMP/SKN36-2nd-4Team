from fastapi import APIRouter


router = APIRouter()


@router.get("/health")
def get_health() -> dict[str, str]:
    """서버가 정상적으로 실행 중인지 확인한다."""
    return {"status": "ok"}

