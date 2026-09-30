from fastapi import APIRouter

from app.api.routes import eda, health, metadata, model, risk_users, summary, survival, users


api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(summary.router, tags=["summary"])
api_router.include_router(risk_users.router, tags=["risk-users"])
api_router.include_router(users.router, tags=["users"])
api_router.include_router(model.router, tags=["model"])
api_router.include_router(metadata.router, tags=["metadata"])
api_router.include_router(eda.router, tags=["eda"])
api_router.include_router(survival.router, tags=["survival"])
