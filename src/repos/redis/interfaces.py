from abc import ABC, abstractmethod
from datetime import timedelta


class AbstractCacheRepository(ABC):
	"""Абстрактный интерфейс для работы с кешем."""

	@abstractmethod
	async def get(self, key: str) -> str | None:
		"""Получает значение из кеша."""
		raise NotImplementedError

	@abstractmethod
	async def set(
		self,
		key: str,
		value: str,
		ttl: int | timedelta | None = None,
	) -> None:
		"""Сохраняет значение в кеш."""
		raise NotImplementedError

	@abstractmethod
	async def delete(self, key: str) -> None:
		"""Удаляет ключ из кеша."""
		raise NotImplementedError

	@abstractmethod
	async def exists(self, key: str) -> bool:
		"""Проверяет существование ключа."""
		raise NotImplementedError

	@abstractmethod
	async def get_many(self, keys: list[str]) -> list[str | None]:
		"""Получает несколько значений за раз."""
		raise NotImplementedError

	@abstractmethod
	async def set_many(
		self,
		mapping: dict[str, str],
		ttl: int | timedelta | None = None,
	) -> None:
		"""Сохраняет несколько значений."""
		raise NotImplementedError
