from fastapi import APIRouter

from src.api.endpoints import routers

router = APIRouter()

for tag, r in routers.items():
	router.include_router(r, tags=[tag])
