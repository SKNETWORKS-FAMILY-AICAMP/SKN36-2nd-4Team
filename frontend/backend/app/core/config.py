import os
from dataclasses import dataclass, field


def _get_frontend_origins() -> list[str]:
    """쉼표로 구분된 환경 변수를 CORS 주소 목록으로 변환한다."""
    raw_origins = os.getenv(
        "FRONTEND_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    )
    return [origin.strip() for origin in raw_origins.split(",") if origin.strip()]


@dataclass(frozen=True)
class Settings:
    """앱 전역에서 사용하는 최소 환경 설정."""

    app_env: str = os.getenv("APP_ENV", "development")
    frontend_origins: list[str] = field(default_factory=_get_frontend_origins)


settings = Settings()

