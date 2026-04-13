"""Startup / shutdown контекст arq-воркера.

ctx — словарь, который arq передаёт в каждую task-функцию.
Здесь создаём все зависимости вручную (без dishka).
"""
import httpx
from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from redis.asyncio import Redis

from src.core.configs import cfg
from src.core.db import create_engine, create_session_factory
from src.core.storages import S3Manager
from src.services.logger import get_logger

logger = get_logger().bind(layer="worker", module="context")


async def startup(ctx: dict) -> None:
	logger.info("worker.startup started")

	engine = create_engine()
	ctx["engine"] = engine
	ctx["session_factory"] = create_session_factory(engine)

	ctx["ml_client"] = httpx.AsyncClient(
		base_url=cfg.ml_service.host,
		headers={"X-Internal-Secret": cfg.ml_service.internal_secret},
		timeout=cfg.ml_service.timeout_seconds,
	)

	ctx["bot"] = Bot(
		token=cfg.bot.token,
		default=DefaultBotProperties(parse_mode=ParseMode.HTML),
	)

	ctx["redis_client"] = Redis(
		host=cfg.redis.host,
		port=cfg.redis.port,
		db=cfg.redis.db,
		password=cfg.redis.password or None,
	)

	ctx["s3_manager"] = S3Manager()

	logger.info("worker.startup done")


async def shutdown(ctx: dict) -> None:
	logger.info("worker.shutdown started")

	await ctx["engine"].dispose()
	await ctx["ml_client"].aclose()
	await ctx["bot"].session.close()
	await ctx["redis_client"].aclose()

	logger.info("worker.shutdown done")
