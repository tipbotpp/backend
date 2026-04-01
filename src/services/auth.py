from __future__ import annotations

import hashlib
import hmac
import json
import uuid
from datetime import timedelta
from typing import cast
from urllib.parse import parse_qsl

import jwt
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.configs import cfg
from src.repos import sql
from src.utils import local_time
from src.repos.redis import sessions_repo
from src.schemas.dataclasses.users import UserCreateDTO, UserDTO


# ── Pure helpers ──────────────────────────────────────────────────────────────

def create_token(telegram_id: int) -> tuple[str, str]:
	"""Создать JWT (RS256). Возвращает (token, jti)."""
	jti = str(uuid.uuid4())
	now = local_time.now()
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
	"""Декодировать и верифицировать JWT публичным ключом."""
	return jwt.decode(
		token,
		cfg.auth.jwt_public_key,
		algorithms=[cfg.auth.jwt_algorithm],
	)


# ── Service ───────────────────────────────────────────────────────────────────

class AuthService:
	def __init__(self, session: AsyncSession, redis: Redis) -> None:
		self._session = session
		self._redis = redis

	async def authenticate(self, init_data: str) -> tuple[UserDTO, bool]:
		"""Валидация initData → получить или создать юзера.

		Возвращает (user_dto, is_new_user). Бросает ValueError при невалидном initData.
		"""
		if cfg.dev.enabled and init_data == cfg.dev.mock_init_data:
			return await self._authenticate_dev_user()

		params = self._validate_init_data(init_data)
		tg_user = self._parse_tg_user(params)

		telegram_id: int = int(cast(int | str, tg_user["id"]))
		username = str(tg_user["username"]) if tg_user.get("username") else None
		display_name = str(tg_user["first_name"]) if tg_user.get("first_name") else None
		avatar_url = str(tg_user["photo_url"]) if tg_user.get("photo_url") else None

		user = await sql.users_repo.get_by_telegram_id(self._session, telegram_id)

		if user is None:
			user = await sql.users_repo.create(
				self._session,
				UserCreateDTO(
					telegram_id=telegram_id,
					username=username,
					display_name=display_name,
					avatar_url=avatar_url,
				),
			)
			return user, True

		user = await sql.users_repo.update_profile(
			self._session,
			telegram_id=telegram_id,
			username=username,
			display_name=display_name,
			avatar_url=avatar_url,
		)
		return user, False

	async def _authenticate_dev_user(self) -> tuple[UserDTO, bool]:
		user = await sql.users_repo.get_by_telegram_id(self._session, cfg.dev.telegram_id)
		if user is not None:
			return user, False
		user = await sql.users_repo.create(
			self._session,
			UserCreateDTO(
				telegram_id=cfg.dev.telegram_id,
				username=cfg.dev.username,
				display_name=cfg.dev.display_name,
			),
		)
		return user, True

	async def create_session(self, telegram_id: int) -> tuple[str, str]:
		"""Создать JWT + записать JTI в Redis. Возвращает (token, jti)."""
		token, jti = create_token(telegram_id)
		await sessions_repo.save(
			self._redis,
			jti,
			telegram_id,
			cfg.auth.jwt_expire_seconds,
		)
		return token, jti

	async def verify_session(self, token: str) -> int:
		"""Проверить JWT + наличие сессии в Redis. Возвращает telegram_id."""
		payload = decode_token(token)
		jti = cast(str, payload["jti"])

		telegram_id = await sessions_repo.get_telegram_id(self._redis, jti)
		if telegram_id is None:
			raise ValueError("Сессия не найдена или истекла")

		return telegram_id

	@staticmethod
	def _validate_init_data(init_data: str) -> dict[str, str]:
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

	@staticmethod
	def _parse_tg_user(params: dict[str, str]) -> dict[str, str | int | None]:
		raw_user = params.get("user")
		if not raw_user:
			raise ValueError("Поле user отсутствует в initData")
		return json.loads(raw_user)
