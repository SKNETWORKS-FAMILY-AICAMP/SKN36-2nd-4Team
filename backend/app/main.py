from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import settings


def create_app() -> FastAPI:
    """FastAPI 애플리케이션을 생성하고 공통 설정을 적용한다."""
    app = FastAPI(
        title="LoL Churn Prediction API",
        version="0.1.0",
        description="LoL 사용자 이탈 예측 대시보드용 API",
    )

    # React 개발 서버가 FastAPI를 호출할 수 있도록 허용한다.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.frontend_origins,
        allow_origin_regex=r"https://.*\.vercel\.app",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router, prefix="/api/v1")
    return app


app = create_app()

