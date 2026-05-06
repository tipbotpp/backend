from __future__ import annotations

from pydantic import Field

from src.schemas.pydantic.common import BaseSchema

_HEX_COLOR_PATTERN = r"^#[0-9A-Fa-f]{6}$"


class AlertSettingsResponse(BaseSchema):
	bg_color: str = Field(description="Цвет фона алерта в формате #RRGGBB")
	text_color: str = Field(description="Цвет текста алерта в формате #RRGGBB")
	font: str = Field(description="Название шрифта (Google Fonts)")
	duration_sec: int = Field(
		description="Длительность показа алерта в секундах",
	)
	image_enabled: bool = Field(
		description="Включена ли генерация изображения к донату",
	)
	tts_enabled: bool = Field(description="Включён ли TTS (озвучка сообщения)")
	tts_voice: str = Field(description="Идентификатор голоса TTS")


class AlertSettingsBody(BaseSchema):
	bg_color: str | None = Field(
		default=None,
		pattern=_HEX_COLOR_PATTERN,
		description="Цвет фона алерта в формате #RRGGBB",
	)
	text_color: str | None = Field(
		default=None,
		pattern=_HEX_COLOR_PATTERN,
		description="Цвет текста алерта в формате #RRGGBB",
	)
	font: str | None = Field(
		default=None,
		min_length=1,
		max_length=64,
		description="Название шрифта (Google Fonts)",
	)
	duration_sec: int | None = Field(
		default=None,
		ge=1,
		le=30,
		description="Длительность показа алерта в секундах (1–30)",
	)
	image_enabled: bool | None = Field(
		default=None,
		description="Включить генерацию изображения к донату",
	)
	tts_enabled: bool | None = Field(
		default=None,
		description="Включить TTS-озвучку сообщения доната",
	)
	tts_voice: str | None = Field(
		default=None,
		min_length=1,
		max_length=64,
		description="Идентификатор голоса TTS (например, silero_v3_ru)",
	)


class AlertTestResponse(BaseSchema):
	status: str = Field(description="Результат отправки: sent")
	message: str = Field(description="Человекочитаемое сообщение")


class GoalResponse(BaseSchema):
	title: str | None = Field(description="Название цели сбора")
	target_amount: int = Field(description="Целевая сумма в монетах")
	current_amount: int = Field(description="Уже собранная сумма в монетах")


class GoalBody(BaseSchema):
	title: str | None = Field(
		default=None,
		min_length=1,
		max_length=128,
		description="Название цели сбора (например, «На новый микрофон»)",
	)
	target_amount: int | None = Field(
		default=None,
		gt=0,
		le=1_000_000,
		description="Целевая сумма в монетах",
	)


class StopWordResponse(BaseSchema):
	id: int = Field(description="ID стоп-слова")
	word: str = Field(description="Стоп-слово в нижнем регистре")


class StopWordBody(BaseSchema):
	word: str = Field(
		min_length=1,
		max_length=64,
		description="Слово для блокировки в сообщениях донатов (регистр не важен)",
	)


class PassiveIncomeResponse(BaseSchema):
	enabled: bool = Field(
		description="Включён ли пассивный доход для зрителей",
	)
	coins_per_interval: int = Field(
		description="Количество монет за один интервал",
	)
	interval_minutes: int = Field(description="Интервал начисления в минутах")


class PassiveIncomeBody(BaseSchema):
	enabled: bool | None = Field(
		default=None,
		description="Включить или отключить пассивный доход",
	)
	coins_per_interval: int | None = Field(
		default=None,
		ge=1,
		le=1_000,
		description="Монет за один интервал (1–1000)",
	)
	interval_minutes: int | None = Field(
		default=None,
		ge=1,
		le=60,
		description="Интервал начисления в минутах (1–60)",
	)
