from collections.abc import AsyncIterator

import httpx
from arq import create_pool
from arq.connections import ArqRedis, RedisSettings
from dishka import Provider, Scope, provide
from redis.asyncio import ConnectionPool, Redis
from sqlalchemy.ext.asyncio import (
	AsyncEngine,
	AsyncSession,
	async_sessionmaker,
)

from src.core.cache import create_redis_client, create_redis_pool
from src.core.configs import cfg
from src.core.db import create_engine, create_session_factory
from src.core.storages import S3Manager
from src.services.logger import AbstractLogger, get_logger


class CoreProvider(Provider):
	scope = Scope.APP  # Создается один раз на всё приложение

	# ========== Database ==========
	@provide
	def get_engine(self) -> AsyncEngine:
		"""Engine живет на всё приложение."""
		return create_engine()

	@provide
	def get_session_factory(
		self,
		engine: AsyncEngine,
	) -> async_sessionmaker[AsyncSession]:
		"""Session factory для создания сессий."""
		return create_session_factory(engine)

	# ========== Redis ==========
	@provide
	def get_redis_pool(self) -> ConnectionPool:
		"""Pool живет на всё приложение."""
		return create_redis_pool()

	@provide
	async def get_redis(self, pool: ConnectionPool) -> Redis:
		"""Redis клиент (APP scope - переиспользуется)."""
		return await create_redis_client(pool)

	# ========== Logger ==========
	@provide
	def get_logger(self) -> AbstractLogger:
		"""Логгер на всё приложение."""
		return get_logger()

	# ========== S3 ==========
	@provide
	def get_s3_manager(self) -> S3Manager:
		"""S3Manager живёт на всё приложение."""
		return S3Manager()

	# ========== ML Service HTTP Client ==========
	@provide
	async def get_ml_client(self) -> AsyncIterator[httpx.AsyncClient]:
		"""HTTP-клиент к ML-сервису. Живёт на всё приложение."""
		async with httpx.AsyncClient(
			base_url=cfg.ml_service.host,
			headers={"X-Internal-Secret": cfg.ml_service.internal_secret},
			timeout=cfg.ml_service.timeout_seconds,
		) as client:
			yield client

	# ========== arq Queue ==========
	@provide
	async def get_arq_pool(self) -> AsyncIterator[ArqRedis]:
		"""arq Redis-пул для постановки задач в очередь."""
		pool = await create_pool(
			RedisSettings(
				host=cfg.redis.host,
				port=cfg.redis.port,
				database=cfg.redis.db,
				password=cfg.redis.password,
			),
		)
		yield pool
		await pool.aclose()


