from __future__ import annotations

from datetime import datetime

from pydantic import Field

from src.schemas.pydantic.common import BaseSchema


class StreamStartBody(BaseSchema):
	passive_income_enabled: bool = Field(
		default=False,
		description="Включить начисление монет зрителям за просмотр стрима",
	)


class StreamStartResponse(BaseSchema):
	session_id: int = Field(description="ID созданной сессии стрима")
	stream_token: str = Field(
		description="Уникальный токен стрима — используется для виджета и WebSocket",
	)
	widget_url: str = Field(
		description="URL OBS Browser Source для подключения виджета",
	)
	ws_url: str = Field(description="WebSocket URL для подключения виджета")
	started_at: datetime = Field(description="Время начала стрима")


class StreamStopResponse(BaseSchema):
	session_id: int = Field(description="ID завершённой сессии стрима")
	total_collected: int = Field(
		description="Итоговая сумма донатов за стрим в монетах",
	)
	donations_count: int = Field(description="Количество донатов за стрим")
	duration_seconds: int = Field(description="Длительность стрима в секундах")
	ended_at: datetime = Field(description="Время завершения стрима")


class StreamStatusResponse(BaseSchema):
	is_live: bool = Field(description="True — стрим активен прямо сейчас")
	session_id: int | None = Field(
		description="ID активной сессии, None если стрим не идёт",
	)
	started_at: datetime | None = Field(
		description="Время начала активного стрима, None если не идёт",
	)
	widget_url: str | None = Field(
		description="URL виджета для OBS, None если стрим не идёт",
	)
