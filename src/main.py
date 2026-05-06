"""Файл для определения точки входа в приложение и его базовой конфигурации"""
from typing import Any, cast

from dishka.integrations.fastapi import setup_dishka
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from src.api import router
from src.core.configs import cfg
from src.core.exc.handlers import ExceptionHandlers
from src.core.middlewares.logging import HTTPLoggingMiddleware
from src.di.container import get_container
from src.lifespan import lifespan

# ========== App ==========
app = FastAPI(lifespan=lifespan, title=cfg.app.title)

# ========== Routers ==========
app.include_router(router)

# ========== Exception handlers ==========
ExceptionHandlers.register(app)

# ========== Middlewares ==========
app.add_middleware(cast(Any, HTTPLoggingMiddleware))
app.add_middleware(
	cast(Any, CORSMiddleware),
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"],
	allow_origins=cfg.app.allow_origins,
)
app.add_middleware(cast(Any, GZipMiddleware))

# ========== Metrics ==========
Instrumentator().instrument(app).expose(app, endpoint="/metrics")

# ========== DI ==========
container = get_container()
setup_dishka(container, app=app)


def main() -> None:
	import uvicorn

	print(f"Starting server on {cfg.app.host}:{cfg.app.port}")
	try:
		if cfg.app.reload or cfg.app.workers > 1:
			uvicorn.run(
				"src.main:app",
				host=cfg.app.host,
				port=cfg.app.port,
				reload=cfg.app.reload,
				reload_dirs=["src"],
				workers=cfg.app.workers,
				access_log=False,
				log_config=None,
				log_level="info",
			)
		else:
			uvicorn.run(
				app,
				host=cfg.app.host,
				port=cfg.app.port,
				access_log=False,
				log_config=None,
				log_level="info",
			)
	except Exception as e:
		print(f"Failed to start server: {e}")
		raise


if __name__ == "__main__":
	main()
