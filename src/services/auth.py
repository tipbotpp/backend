from __future__ import annotations

import hashlib
import hmac
import json
import uuid
from datetime import UTC, datetime, timedelta
from urllib.parse import parse_qsl

import jwt
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.configs import cfg
from src.repos import sql
from src.repos.redis import sessions_repo
from src.schemas.dataclasses.users import UserCreateDTO, UserDTO

_VIEWER_START_BALANCE = 100


def _validate_init_data(init_data: str) -> dict[str, str]:
	"""
	Валидация Telegram WebApp initData через HMAC-SHA256.

	https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app
	"""
	params = dict(parse_qsl(init_data, keep_blank_values=True))
	received_hash = params.pop("hash", None)
	if not received_hash:
		raise ValueError("hash отсутствует в initData")

	data_check_string = "\n".join(
		f"{k}={v}" for k, v in sorted(params.items())
	)

	secret_key = hmac.new(
		b"WebAppData",
		cfg.bot.token.encode(),
		hashlib.sha256,
	).digest()
	computed_hash = hmac.new(
		secret_key,
		data_check_string.encode(),
		hashlib.sha256,
	).hexdigest()

	if not hmac.compare_digest(computed_hash, received_hash):
		raise ValueError("Невалидная подпись initData")

	return params


def _parse_tg_user(params: dict[str, str]) -> dict[str, str | int | None]:
	"""Парсим поле user из initData (JSON-строка)."""
	raw_user = params.get("user")
	if not raw_user:
		raise ValueError("Поле user отсутствует в initData")
	return json.loads(raw_user)


def create_token(telegram_id: int) -> tuple[str, str]:
	"""
	Создать JWT (RS256). Возвращает (token, jti).

	Подписывается приватным ключом; верифицировать можно публичным.
	"""
	jti = str(uuid.uuid4())
	now = datetime.now(UTC)
	payload = {
		"sub": str(telegram_id),
		"jti": jti,
		"iat": now,
		"exp": now + timedelta(seconds=cfg.auth.jwt_expire_seconds),
	}
	token = jwt.encode(
		payload,
		cfg.auth.jwt_private_key,
		algorithm=cfg.auth.jwt_algorithm,
	)
	return token, jti


def decode_token(token: str) -> dict[str, object]:
	"""
	Декодировать и верифицировать JWT публичным ключом.
	Бросает jwt.PyJWTError при невалидном/истёкшем токене.
	"""
	return jwt.decode(
		token,
		cfg.auth.jwt_public_key,
		algorithms=[cfg.auth.jwt_algorithm],
	)


async def authenticate(
	session: AsyncSession,
	redis_client: object,
	init_data: str,
) -> tuple[UserDTO, bool]:
	"""
	Валидация initData → получить или создать юзера.
	Возвращает (user_dto, is_new_user).
	"""
	params = _validate_init_data(init_data)
	tg_user = _parse_tg_user(params)

	telegram_id: int = int(tg_user["id"])
	user = await sql.users_repo.get_by_telegram_id(session, telegram_id)

	if user is not None:
		return user, False

	dto = UserCreateDTO(
		telegram_id=telegram_id,
		username=tg_user.get("username"),
		display_name=tg_user.get("first_name"),
	)
	user = await sql.users_repo.create(session, dto)
	return user, True


async def create_session(
	redis_client: object,
	telegram_id: int,
) -> tuple[str, str]:
	"""
	Создать JWT + записать JTI в Redis.
	Возвращает (token, jti).
	"""
	token, jti = create_token(telegram_id)
	await sessions_repo.save(
		redis_client,
		jti,
		telegram_id,
		cfg.auth.jwt_expire_seconds,
	)
	return token, jti


async def verify_session(
	redis_client: object,
	token: str,
) -> int:
	"""
	Проверить JWT + наличие сессии в Redis.
	Возвращает telegram_id или бросает исключение.
	"""
	payload = decode_token(token)
	jti: str = payload["jti"]  # type: ignore[assignment]

	telegram_id = await sessions_repo.get_telegram_id(redis_client, jti)
	if telegram_id is None:
		raise ValueError("Сессия не найдена или истекла")

	return telegram_id
