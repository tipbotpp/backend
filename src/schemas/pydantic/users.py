from __future__ import annotations

from datetime import datetime

from fastapi import Query
from pydantic import Field

from src.schemas.pydantic.common import (
    BaseSchema,
    Paginated,
    PaginationFilters,
)


class UserResponse(BaseSchema):
    telegram_id: int = Field(description="Telegram ID пользователя")
    username: str | None = Field(description="Telegram username (без @)")
    display_name: str | None = Field(description="Отображаемое имя (кастомное или из Telegram)")
    avatar_url: str | None = Field(description="URL аватара из Telegram")
    role: str | None = Field(description="Роль: viewer | streamer. None — не выбрана")
    balance: int = Field(description="Баланс в монетах")
    created_at: datetime = Field(description="Дата регистрации")


class UserUpdateBody(BaseSchema):
    display_name: str | None = Field(
        default=None,
        min_length=1,
        max_length=64,
        description="Отображаемое имя. После установки перестаёт обновляться из Telegram",
    )
    description: str | None = Field(
        default=None,
        max_length=500,
        description="Описание профиля (отображается на странице стримера)",
    )


class UserRoleBody(BaseSchema):
    role: str = Field(
        pattern="^(viewer|streamer)$",
        description="Роль пользователя: viewer или streamer. Устанавливается один раз",
    )


class UserRoleResponse(BaseSchema):
    telegram_id: int = Field(description="Telegram ID пользователя")
    role: str = Field(description="Установленная роль: viewer | streamer")
    balance: int = Field(description="Начальный баланс (100 монет для viewer, 0 для streamer)")


class GoalPreview(BaseSchema):
    title: str | None = Field(description="Название цели сбора")
    target_amount: int = Field(description="Целевая сумма в монетах")
    current_amount: int = Field(description="Уже собранная сумма в монетах")


class AlertPreview(BaseSchema):
    bg_color: str = Field(description="Цвет фона алерта в формате #RRGGBB")
    text_color: str = Field(description="Цвет текста алерта в формате #RRGGBB")
    font: str = Field(description="Название шрифта")
    duration_sec: int = Field(description="Длительность показа алерта в секундах")


class StreamerItemResponse(BaseSchema):
    telegram_id: int = Field(description="Telegram ID стримера")
    username: str | None = Field(description="Telegram username (без @)")
    display_name: str | None = Field(description="Отображаемое имя")
    avatar_url: str | None = Field(description="URL аватара")
    is_live: bool = Field(description="True — стрим активен прямо сейчас")
    goal: GoalPreview | None = Field(description="Текущая цель сбора, если задана")


class StreamerListResponse(Paginated[StreamerItemResponse]):
    pass


class StreamerProfileResponse(BaseSchema):
    telegram_id: int = Field(description="Telegram ID стримера")
    username: str | None = Field(description="Telegram username (без @)")
    display_name: str | None = Field(description="Отображаемое имя")
    avatar_url: str | None = Field(description="URL аватара")
    description: str | None = Field(description="Описание профиля")
    is_live: bool = Field(description="True — стрим активен прямо сейчас")
    goal: GoalPreview | None = Field(description="Текущая цель сбора, если задана")
    alert_preview: AlertPreview | None = Field(description="Настройки стиля алерта для превью виджета")


class StreamerFilters(PaginationFilters):
    search: str | None = Query(
        default=None,
        min_length=1,
        max_length=100,
        description="Поиск по username или display_name стримера",
    )
