from collections.abc import AsyncGenerator
from typing import Any

from dishka import Provider, Scope, provide
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.core.config import cfg
from src.models.user import User
from src.repos.redis.example import CacheRepository
from src.repos.redis.interfaces import AbstractCacheRepository
from src.repos.s3.example import PhotoRepository
from src.repos.s3.interfaces import AbstractS3Repository
from src.repos.sql.example import UserRepository
from src.repos.sql.interfaces import AbstractBaseRepository


class RepositoryProvider(Provider):
	scope = Scope.REQUEST  # Новый на каждый запрос

	@provide
	async def get_session(
		self,
		factory: async_sessionmaker[AsyncSession],
	) -> AsyncGenerator[AsyncSession, None]:
		async with factory() as session:
			async with session.begin():
				yield session

	@provide
	def get_user_repo(self, session: AsyncSession) -> AbstractBaseRepository[User]:
		return UserRepository(session)

	@provide
	def get_cache_repo(self, redis: Redis) -> AbstractCacheRepository:
		return CacheRepository(redis)

	@provide
	def get_s3_repo(self, s3_client: Any) -> AbstractS3Repository:
		return PhotoRepository(s3_client, cfg.s3.aws_bucket)
