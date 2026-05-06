from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.models.users import Users


class UserMiddleware(BaseMiddleware):
	"""
	Middleware для автоматической регистрации/обновления пользователя в БД.
	Добавляет объект User в data["user"] для использования в хендлерах.
	"""

	def __init__(
		self,
		session_factory: async_sessionmaker[AsyncSession],
	) -> None:
		self.session_factory = session_factory

	async def __call__(
		self,
		handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
		event: TelegramObject,
		data: dict[str, Any],
	) -> Any:
		tg_user = data.get("event_from_user")
		if tg_user is None:
			return await handler(event, data)

		async with self.session_factory() as session:
			async with session.begin():
				user = await session.scalar(
					select(Users).where(Users.telegram_id == tg_user.id),
				)

				if user is None:
					user = Users(
						telegram_id=tg_user.id,
						username=tg_user.username,
						display_name=tg_user.full_name,
					)
					session.add(user)
					try:
						await session.flush()
					except IntegrityError:
						await session.rollback()
						user = await session.scalar(
							select(Users).where(
								Users.telegram_id == tg_user.id,
							),
						)
						if user is None:
							raise
				else:
					changed = False
					if user.username != tg_user.username:
						user.username = tg_user.username
						changed = True
					if (
						not user.display_name_custom
						and user.display_name != tg_user.full_name
					):
						user.display_name = tg_user.full_name
						changed = True
					if changed:
						await session.flush()

				data["user"] = user

		return await handler(event, data)
