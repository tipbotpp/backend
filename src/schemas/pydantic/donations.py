from __future__ import annotations

from datetime import datetime

from fastapi import Query
from pydantic import Field

from src.schemas.pydantic.common import (
	BaseSchema,
	Paginated,
	PaginationFilters,
)


class DonationBody(BaseSchema):
	streamer_id: int = Field(
		gt=0,
		description="Telegram ID стримера-получателя",
	)
	amount: int = Field(gt=0, le=10_000, description="Сумма доната в монетах")
	message: str | None = Field(
		default=None,
		min_length=1,
		max_length=500,
		description="Текст сообщения к донату. Проходит модерацию (токсичность + стоп-слова)",
	)


class DonationCreateResponse(BaseSchema):
	donation_id: int = Field(description="ID созданного доната")
	status: str = Field(
		description="Статус доната: processing | completed | rejected",
	)
	message: str = Field(description="Человекочитаемое сообщение о результате")


class DonorResponse(BaseSchema):
	id: int = Field(description="Telegram ID пользователя")
	username: str | None = Field(description="Telegram username (без @)")


class DonationHistoryItemResponse(BaseSchema):
	id: int = Field(description="ID доната")
	amount: int = Field(description="Сумма в монетах")
	message: str | None = Field(description="Текст сообщения к донату")
	status: str = Field(
		description="Статус: processing | completed | rejected",
	)
	audio_url: str | None = Field(
		description="Presigned URL на TTS-аудио (временный)",
	)
	image_url: str | None = Field(
		description="Presigned URL на сгенерированное изображение (временный)",
	)
	from_user: DonorResponse = Field(description="Отправитель доната")
	to_streamer: DonorResponse = Field(
		description="Получатель доната (стример)",
	)
	created_at: datetime = Field(description="Дата и время создания доната")


class DonationHistoryResponse(Paginated[DonationHistoryItemResponse]):
	pass


class TopDonatorResponse(BaseSchema):
	username: str | None = Field(description="Telegram username топ-донатера")
	total_amount: int = Field(description="Суммарная сумма донатов за сессию")


class TimelineItemResponse(BaseSchema):
	time: str = Field(description="Временная метка (формат HH:MM)")
	amount: int = Field(description="Сумма донатов в эту минуту")


class SessionStatsResponse(BaseSchema):
	session_id: int = Field(description="ID текущей сессии стрима")
	total_collected: int = Field(
		description="Итоговая сумма донатов за сессию в монетах",
	)
	donations_count: int = Field(description="Количество донатов за сессию")
	top_donator: TopDonatorResponse | None = Field(
		description="Топ-донатер сессии, None если донатов не было",
	)
	timeline: list[TimelineItemResponse] = Field(
		description="Динамика донатов по минутам",
	)


class DonationHistoryFilters(PaginationFilters):
	type: str | None = Query(
		default=None,
		pattern="^(sent|received)$",
		description="Фильтр по направлению: sent — отправленные, received — полученные. Без фильтра — все",
	)
