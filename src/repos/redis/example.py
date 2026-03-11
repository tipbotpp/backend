from redis.asyncio import Redis
from datetime import timedelta

from .interfaces import AbstractCacheRepository


class CacheRepository(AbstractCacheRepository):
	"""Реализация кеш репозитория на Redis."""

	def __init__(self, redis: Redis) -> None:
		self.redis = redis

	async def get(self, key: str) -> str | None:
		return await self.redis.get(key)

	async def set(
		self,
		key: str,
		value: str,
		ttl: int | timedelta | None = None,
	) -> None:
		await self.redis.set(key, value, ex=ttl)

	async def delete(self, key: str) -> None:
		await self.redis.delete(key)

	async def exists(self, key: str) -> bool:
		return bool(await self.redis.exists(key))

	async def get_many(self, keys: list[str]) -> list[str | None]:
		if not keys:
			return []
		return await self.redis.mget(keys)

	async def set_many(
		self,
		mapping: dict[str, str],
		ttl: int | timedelta | None = None,
	) -> None:
		if not mapping:
			return

		async with self.redis.pipeline() as pipe:
			for key, value in mapping.items():
				await pipe.set(key, value, ex=ttl)
			await pipe.execute()
