from __future__ import annotations

from src.schemas.pydantic.common import BaseSchema


class TelegramAuthBody(BaseSchema):
	init_data: str


class AuthUserResponse(BaseSchema):
	telegram_id: int
	username: str | None
	role: str | None
	balance: int


class AuthResponse(BaseSchema):
	access_token: str
	token_type: str = "bearer"
	is_new_user: bool
	user: AuthUserResponse
