from __future__ import annotations

from pydantic import Field

from src.schemas.pydantic.common import BaseSchema


class TelegramAuthBody(BaseSchema):
    init_data: str = Field(min_length=1, description="Строка initData из window.Telegram.WebApp.initData")


class AuthUserResponse(BaseSchema):
    telegram_id: int = Field(description="Telegram ID пользователя")
    username: str | None = Field(description="Telegram username (без @), может отсутствовать")
    role: str | None = Field(description="Роль пользователя: viewer | streamer. None — роль ещё не выбрана")
    balance: int = Field(description="Баланс в монетах")


class AuthResponse(BaseSchema):
    is_new_user: bool = Field(description="True — пользователь зарегистрирован впервые")
    user: AuthUserResponse = Field(description="Базовые данные пользователя")
