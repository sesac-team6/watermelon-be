from fastapi import APIRouter

from app.api.v1.endpoints import database, health, prices

api_router = APIRouter()
api_router.include_router(database.router, prefix="/database", tags=["database"])
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(prices.router, prefix="/prices", tags=["prices"])
