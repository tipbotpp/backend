from __future__ import annotations

import jwt
from dishka.integrations.fastapi import FromDishka, inject
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exc.exceptions import InvalidTokenError, UserNotFoundError
from src.repos import sql
from src.schemas.dataclasses.users import UserDTO
from src.services import auth as auth_service

_bearer = HTTPBearer()


@inject
async def get_current_user(
	credentials: HTTPAuthorizationCredentials = Depends(_bearer),
	session: FromDishka[AsyncSession] = ...,  # type: ignore[assignment]
	redis: FromDishka[Redis] = ...,  # type: ignore[assignment]
) -> UserDTO:
	try:
		telegram_id = await auth_service.verify_session(
			redis,
			credentials.credentials,
		)
	except (jwt.PyJWTError, ValueError):
		raise InvalidTokenError

	user = await sql.users_repo.get_by_telegram_id(session, telegram_id)
	if user is None:
		raise UserNotFoundError

	return user
