"""Жизненный цикл приложения"""
import asyncio
import contextlib
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from aiogram import Bot, Dispatcher
from dishka import AsyncContainer
from dishka.integrations.aiogram import setup_dishka as setup_dishka_aiogram
from fastapi import FastAPI

from src.bot.handlers import router as bot_router
from src.core.configs import cfg
from src.core.db import create_engine, create_session_factory
from src.core.exc.handlers import error_router
from src.core.middlewares.logging import LoggingMiddleware
from src.core.middlewares.user import UserMiddleware
from src.services.logger import AbstractLogger, get_logger

logger: AbstractLogger = get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
	logger.info("Starting lifespan")

	# ========== DI ==========
	container: AsyncContainer = app.state.dishka_container

	# ========== Database ==========
	engine = create_engine()
	session_factory = create_session_factory(engine)

	# ========== Bot ==========
	bot = Bot(token=cfg.bot.token)
	dp = Dispatcher()

	dp.update.outer_middleware(LoggingMiddleware())
	dp.update.outer_middleware(UserMiddleware(session_factory))

	dp.include_router(error_router)
	dp.include_router(bot_router)

	setup_dishka_aiogram(container=container, router=dp)

	polling_task = asyncio.create_task(
		dp.start_polling(bot, drop_pending_updates=cfg.bot.drop_pending_updates),
	)
	logger.info("Bot started")

	try:
		yield
	finally:
		logger.info("Stopping lifespan")
		polling_task.cancel()
		with contextlib.suppress(asyncio.CancelledError):
			await polling_task
		await bot.session.close()
		await engine.dispose()
		await container.close()
		logger.info("Bot stopped")
