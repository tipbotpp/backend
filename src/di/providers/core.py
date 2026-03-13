from collections.abc import AsyncIterator
from typing import Any

from dishka import Provider, Scope, provide
from redis.asyncio import ConnectionPool, Redis
from sqlalchemy.ext.asyncio import (
	AsyncEngine,
	AsyncSession,
	async_sessionmaker,
)

from src.core.cache import create_redis_client, create_redis_pool
from src.core.db import create_engine, create_session_factory
from src.core.storages import get_s3_client, get_s3_external_client
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


class RequestProvider(Provider):
	scope = Scope.REQUEST

	@provide
	async def get_s3_client(self) -> AsyncIterator[Any]:
		"""Provide S3 клиента на время запроса."""
		async with get_s3_client() as client:
			yield client  # Dishka автоматически закроет после REQUEST

	@provide
	async def get_s3_external_client(self) -> AsyncIterator[Any]:
		"""Provide S3 клиента на время запроса."""
		async with get_s3_external_client() as client:
			yield client  # Dishka автоматически закроет после REQUEST
