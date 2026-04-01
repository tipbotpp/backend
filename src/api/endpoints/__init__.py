from fastapi import APIRouter

from src.api.endpoints.auth import router as auth_router
from src.api.endpoints.balance import router as balance_router
from src.api.endpoints.health import router as health_router
from src.api.endpoints.jwks import router as jwks_router
from src.api.endpoints.users import router as users_router

routers: dict[str, APIRouter] = {
	"Auth": auth_router,
	"Users": users_router,
	"Balance": balance_router,
	"JWKS": jwks_router,
	"Health": health_router,
}
