import asyncio
import time
from collections import defaultdict
from collections.abc import Awaitable, Callable, Hashable
from typing import Any, ParamSpec, TypeVar

P = ParamSpec("P")
T = TypeVar("T")


def async_ttl_cache(
	ttl_seconds: int,
	key_fn: Callable[..., Hashable],
) -> Callable[[Callable[P, Awaitable[T]]], Callable[P, Awaitable[T]]]:
	"""
	Декоратор для кеширования результатов async функций в памяти с TTL.

	Использование:
		@async_ttl_cache(ttl_seconds=60, key_fn=lambda user_id: f"user:{user_id}")
		async def get_user_permissions(user_id: int) -> list[str]:
			return await slow_external_api.fetch_permissions(user_id)

	Args:
		ttl_seconds: Время жизни кеша в секундах
		key_fn: Функция для генерации ключа кеша из аргументов

	Note:
		- Кеш per-instance (не shared между воркерами)
		- Используй Redis для shared cache
	"""
	cache: dict[Hashable, tuple[float, Any]] = {}
	locks: defaultdict[Hashable, asyncio.Lock] = defaultdict(asyncio.Lock)

	def is_fresh(expires_at: float) -> bool:
		return time.time() < expires_at

	def decorator(
		func: Callable[P, Awaitable[T]],
	) -> Callable[P, Awaitable[T]]:
		async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
			key: Hashable = key_fn(*args, **kwargs)
			now: float = time.time()

			if (item := cache.get(key)) is not None:
				expires_at, value = item
				if is_fresh(expires_at):
					return value

			async with locks[key]:
				item = cache.get(key)
				if item is not None:
					expires_at, value = item
					if is_fresh(expires_at):
						return value

				value = await func(*args, **kwargs)
				cache[key] = (now + ttl_seconds, value)
				return value

		return wrapper

	return decorator
