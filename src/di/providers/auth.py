from __future__ import annotations

import jwt
from dishka import Provider, Scope, provide
from fastapi import Request
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exc.exceptions import InvalidTokenError, UserNotFoundError
from src.repos import sql
from src.schemas.dataclasses.users import UserDTO
from src.services import auth as auth_service


class AuthProvider(Provider):
	@provide(scope=Scope.REQUEST)
	async def get_current_user(
		self,
		request: Request,
		session: AsyncSession,
		redis: Redis,
	) -> UserDTO:
		auth_header = request.headers.get("Authorization")
		if not auth_header or not auth_header.startswith("Bearer "):
			raise InvalidTokenError

		token = auth_header.removeprefix("Bearer ").strip()

		try:
			telegram_id = await auth_service.verify_session(redis, token)
		except (jwt.PyJWTError, ValueError):
			raise InvalidTokenError

		user = await sql.users_repo.get_by_telegram_id(session, telegram_id)
		if user is None:
			raise UserNotFoundError

		return user
