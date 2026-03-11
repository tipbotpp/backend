from fastapi import APIRouter

from src.api.v1.endpoints import routers

api_router = APIRouter(prefix="/api/v1")

for tag, router in routers.items():
	api_router.include_router(router, tags=[tag])
