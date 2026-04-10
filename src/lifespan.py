"""Жизненный цикл приложения"""
import asyncio
import contextlib
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from dishka import AsyncContainer
from dishka.integrations.aiogram import setup_dishka as setup_dishka_aiogram
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import async_sessionmaker

from src.bot.handlers import router as bot_router
from src.core.configs import cfg
from src.core.db import create_engine, create_session_factory
from src.core.exc.handlers import error_router
from src.core.middlewares.logging import LoggingMiddleware
from src.core.middlewares.user import UserMiddleware
from src.repos import sql
from src.schemas.dataclasses.users import UserCreateDTO
from src.services.logger import AbstractLogger, get_logger

logger: AbstractLogger = get_logger()


async def _ensure_dev_user(session_factory: async_sessionmaker) -> None:
	async with session_factory() as session:
		existing = await sql.users_repo.get_by_telegram_id(session, cfg.dev.telegram_id)
		if existing is None:
			await sql.users_repo.create(
				session,
				UserCreateDTO(
					telegram_id=cfg.dev.telegram_id,
					username=cfg.dev.username,
					display_name=cfg.dev.display_name,
				),
			)
			await session.commit()
			logger.info("Dev user created", telegram_id=cfg.dev.telegram_id)
		else:
			logger.info("Dev user already exists", telegram_id=cfg.dev.telegram_id)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
	logger.info("Starting lifespan")

	# ========== DI ==========
	container: AsyncContainer = app.state.dishka_container

	# ========== Database ==========
	engine = create_engine()
	session_factory = create_session_factory(engine)

	# ========== Dev user ==========
	if cfg.dev.enabled:
		await _ensure_dev_user(session_factory)

	# ========== Bot ==========
	bot = Bot(token=cfg.bot.token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
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
