from __future__ import annotations

from redis.asyncio import Redis

_KEY_PREFIX = "session:"


def _key(jti: str) -> str:
	return f"{_KEY_PREFIX}{jti}"


async def save(redis: Redis, jti: str, telegram_id: int, ttl: int) -> None:
	"""Сохранить сессию. TTL = время жизни JWT в секундах."""
	await redis.set(_key(jti), telegram_id, ex=ttl)


async def get_telegram_id(redis: Redis, jti: str) -> int | None:
	"""Вернуть telegram_id по JTI или None если сессия не существует / истекла."""
	value = await redis.get(_key(jti))
	if value is None:
		return None
	return int(value)


async def delete(redis: Redis, jti: str) -> None:
	"""Отозвать сессию (logout)."""
	await redis.delete(_key(jti))
