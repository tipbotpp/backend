from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, func
from sqlalchemy.orm import (
	Mapped,
	mapped_column,
)

if TYPE_CHECKING:
	from sqlalchemy.ext.asyncio import AsyncSession


class TimestampMixin:
	"""Миксин для автоматических полей created_at / updated_at."""

	created_at: Mapped[datetime] = mapped_column(
		DateTime(timezone=True),
		default=lambda: datetime.now(UTC),
		server_default=func.now(),
	)
	updated_at: Mapped[datetime] = mapped_column(
		DateTime(timezone=True),
		default=lambda: datetime.now(UTC),
		server_default=func.now(),
		onupdate=lambda: datetime.now(UTC),
		server_onupdate=func.now(),
	)


class SoftDeleteMixin:
	"""Миксин для добавления функционала мягкого удаления"""

	deleted_at: Mapped[datetime | None] = mapped_column(
		DateTime(timezone=True),
		nullable=True,
		default=None,
		server_default=None,
	)

	async def soft_delete(self, session: "AsyncSession") -> None:
		"""Мягкое удаление записи (установка deleted_at)."""
		self.deleted_at = datetime.now(UTC)
		session.add(self)
		await session.commit()

	async def restore(self, session: "AsyncSession") -> None:
		"""Восстановление мягко удаленной записи."""
		self.deleted_at = None
		session.add(self)
		await session.commit()

	@property
	def is_deleted(self) -> bool:
		"""Проверка, удалена ли запись."""
		return self.deleted_at is not None