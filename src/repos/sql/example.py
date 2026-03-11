from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.user import User

from .base import BaseRepository


class UserRepository(BaseRepository[User]):
	"""
	Репозиторий для работы с пользователями.
	Наследуется от BaseRepository для базовых CRUD операций.
	"""

	def __init__(self, session: AsyncSession) -> None:
		super().__init__(session, User)

	async def get_by_email(self, email: str) -> User | None:
		"""
		Поиск пользователя по email.

		:param email: Email пользователя
		:return: User или None
		"""
		result = await self.session.execute(
			select(User).where(User.email == email),
		)
		return result.scalar_one_or_none()

	async def exists_by_email(self, email: str) -> bool:
		"""
		Проверка существования пользователя по email.

		:param email: Email пользователя
		:return: True если существует
		"""
		result = await self.session.execute(
			select(User.id).where(User.email == email),
		)
		return result.scalar_one_or_none() is not None
