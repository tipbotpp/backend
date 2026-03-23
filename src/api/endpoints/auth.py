from __future__ import annotations

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exc.exceptions import InvalidInitDataError
from src.schemas.pydantic import auth as auth_schema
from src.services import auth as auth_service
from src.utils.mappers import map_model

router = APIRouter(prefix="/auth", route_class=DishkaRoute)


@router.post("/telegram", response_model=auth_schema.AuthResponse)
async def telegram_auth(
	body: auth_schema.TelegramAuthBody,
	session: FromDishka[AsyncSession],
	redis: FromDishka[Redis],
) -> auth_schema.AuthResponse:
	"""Авторизация через Telegram Mini App initData → JWT."""
	try:
		user, is_new_user = await auth_service.authenticate(
			session,
			redis,
			body.init_data,
		)
	except ValueError:
		raise InvalidInitDataError

	token, _ = await auth_service.create_session(redis, user.telegram_id)

	return auth_schema.AuthResponse(
		access_token=token,
		is_new_user=is_new_user,
		user=map_model(user, auth_schema.AuthUserResponse),
	)
