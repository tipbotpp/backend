from __future__ import annotations

from dishka.integrations.fastapi import DishkaRoute, FromDishka, inject
from fastapi import APIRouter, Response

from src.core.configs import cfg
from src.core.exc.exceptions import InvalidInitDataError
from src.schemas.pydantic import auth as auth_schema
from src.services.auth import AuthService
from src.services.logger import get_logger
from src.utils.mappers import map_model

router = APIRouter(prefix="/auth", route_class=DishkaRoute)

logger = get_logger().bind(layer="endpoint", module="auth")


@router.post("/telegram", response_model=auth_schema.AuthResponse, summary="Авторизация через Telegram Mini App")
@inject
async def telegram_auth(
	body: auth_schema.TelegramAuthBody,
	response: Response,
	auth_service: FromDishka[AuthService],
) -> auth_schema.AuthResponse:
	"""Авторизация через Telegram Mini App.

	Валидирует `initData` из Telegram WebApp, создаёт или обновляет пользователя,
	выдаёт JWT в httpOnly cookie `access_token`.

	Args:
		body: Объект с полем `init_data` — строка initData из `window.Telegram.WebApp`.

	Returns:
		AuthResponse: Флаг `is_new_user` и базовые данные пользователя.

	Raises:
		400: Неверная подпись `initData` (невалидный токен или данные подделаны).
	"""
	log = logger.bind(
		request_init_data_length=len(body.init_data),
		request_init_data=body.init_data,
	)
	log.debug("POST /auth/telegram")

	try:
		user, is_new_user = await auth_service.authenticate(body.init_data)
	except ValueError:
		log.error("auth failed: invalid init_data")
		raise InvalidInitDataError

	token, _ = await auth_service.create_session(user.telegram_id)

	response.set_cookie(
		key="access_token",
		value=token,
		httponly=True,
		secure=not cfg.dev.enabled,
		samesite="none" if not cfg.dev.enabled else "lax",
		max_age=cfg.auth.jwt_expire_seconds,
	)

	log.info(
		"auth success",
		user_id=user.telegram_id,
		username=user.username,
		is_new_user=is_new_user,
	)
	return auth_schema.AuthResponse(
		is_new_user=is_new_user,
		user=map_model(user, auth_schema.AuthUserResponse),
	)
