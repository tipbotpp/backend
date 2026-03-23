from fastapi import APIRouter

from src.api.v1.endpoints.auth import router as auth_router
from src.api.v1.endpoints.jwks import router as jwks_router
from src.api.v1.endpoints.users import router as users_router

routers: dict[str, APIRouter] = {
	"Auth": auth_router,
	"Users": users_router,
	"JWKS": jwks_router,
}
