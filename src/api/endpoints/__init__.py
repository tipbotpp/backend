from fastapi import APIRouter

from src.api.endpoints.auth import router as auth_router
from src.api.endpoints.balance import router as balance_router
from src.api.endpoints.donations import router as donations_router
from src.api.endpoints.health import router as health_router
from src.api.endpoints.jwks import router as jwks_router
from src.api.endpoints.settings import router as settings_router
from src.api.endpoints.stream import router as stream_router
from src.api.endpoints.users import router as users_router
from src.api.endpoints.widget import router as widget_router
from src.api.endpoints.ws import router as ws_router
from src.api.endpoints.ws_viewer import router as ws_viewer_router

routers: dict[str, APIRouter] = {
	"Auth": auth_router,
	"Users": users_router,
	"Balance": balance_router,
	"Donations": donations_router,
	"Stream": stream_router,
	"Settings": settings_router,
	"WebSocket": ws_router,
	"WebSocket Viewer": ws_viewer_router,
	"Widget": widget_router,
	"JWKS": jwks_router,
	"Health": health_router,
}
