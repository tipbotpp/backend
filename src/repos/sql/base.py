from typing import Generic

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .interfaces import AbstractBaseRepository, ModelT


class BaseRepository(AbstractBaseRepository[ModelT], Generic[ModelT]):
	"""
	Базовая реализация SQL репозитория с CRUD операциями.
	"""

	def __init__(self, session: AsyncSession, model: type[ModelT]) -> None:
		self.session = session
		self.model = model

	async def get_by_id(self, id: int) -> ModelT | None:
		result = await self.session.execute(
			select(self.model).where(self.model.id == id),
		)
		return result.scalar_one_or_none()

	async def get_all(
		self,
		limit: int = 100,
		offset: int = 0,
	) -> list[ModelT]:
		result = await self.session.execute(
			select(self.model).limit(limit).offset(offset),
		)
		return list(result.scalars().all())

	async def create(self, **kwargs) -> ModelT:
		instance = self.model(**kwargs)
		self.session.add(instance)
		await self.session.flush()
		await self.session.refresh(instance)
		return instance

	async def update(self, instance: ModelT, **kwargs) -> ModelT:
		for key, value in kwargs.items():
			setattr(instance, key, value)
		await self.session.flush()
		await self.session.refresh(instance)
		return instance

	async def delete(self, instance: ModelT) -> None:
		await self.session.delete(instance)
		await self.session.flush()
