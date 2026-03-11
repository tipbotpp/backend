from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from src.models.base import Base

ModelT = TypeVar("ModelT", bound=Base)


class AbstractBaseRepository(ABC, Generic[ModelT]):
	"""
	Абстрактный базовый репозиторий.
	Определяет стандартные CRUD операции для всех SQL репозиториев.
	"""

	@abstractmethod
	async def get_by_id(self, id: int) -> ModelT | None:
		"""Получает запись по ID."""
		raise NotImplementedError

	@abstractmethod
	async def get_all(
		self,
		limit: int = 100,
		offset: int = 0,
	) -> list[ModelT]:
		"""Получает все записи с пагинацией."""
		raise NotImplementedError

	@abstractmethod
	async def create(self, **kwargs) -> ModelT:
		"""Создает новую запись."""
		raise NotImplementedError

	@abstractmethod
	async def update(self, instance: ModelT, **kwargs) -> ModelT:
		"""Обновляет существующую запись."""
		raise NotImplementedError

	@abstractmethod
	async def delete(self, instance: ModelT) -> None:
		"""Удаляет запись."""
		raise NotImplementedError
