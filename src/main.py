from typing import Any, cast

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from src.core.config import cfg
from src.core.exc.handlers import ExceptionHandlers
from src.core.middlewares.logging import HTTPLoggingMiddleware
from src.lifespan import lifespan

app = FastAPI(lifespan=lifespan, title=cfg.app.title)

# Exception handlers
ExceptionHandlers.register(app)

# Routers
from src.api import router_v1

app.include_router(router_v1)

# Middlewares
app.add_middleware(cast(Any, HTTPLoggingMiddleware))
app.add_middleware(
	cast(Any, CORSMiddleware),
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"],
	allow_origins=cfg.app.allow_origins,
)
app.add_middleware(cast(Any, GZipMiddleware))


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
