from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from dishka.integrations.fastapi import setup_dishka
from fastapi import FastAPI

from src.di.container import get_container
from src.services.logger import AbstractLogger, get_logger

logger: AbstractLogger = get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
	logger.info("Starting lifespan")

	# DI container
	container = get_container()
	setup_dishka(container, app)

	try:
		yield
	finally:
		logger.info("Stopping lifespan")
		await container.close()
