from __future__ import annotations

from dishka import Provider, Scope, provide
from fastapi import Request
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exc.exceptions import InvalidTokenError
from src.schemas.dataclasses.users import UserDTO
from src.services.auth import get_user_from_cookie


class AuthProvider(Provider):
    @provide(scope=Scope.REQUEST)
    async def get_current_user(
        self,
        request: Request,
        session: AsyncSession,
        redis: Redis,
    ) -> UserDTO:
        user = await get_user_from_cookie(
            request.cookies.get("access_token"),
            session,
            redis,
        )
        if user is None:
            raise InvalidTokenError
        return user
