from __future__ import annotations

from src.schemas.pydantic.common import BaseSchema


class AlertSettingsResponse(BaseSchema):
	bg_color: str
	text_color: str
	font: str
	duration_sec: int
	image_enabled: bool
	tts_enabled: bool
	tts_voice: str


class AlertSettingsBody(BaseSchema):
	bg_color: str | None = None
	text_color: str | None = None
	font: str | None = None
	duration_sec: int | None = None
	image_enabled: bool | None = None
	tts_enabled: bool | None = None
	tts_voice: str | None = None


class AlertTestResponse(BaseSchema):
	status: str
	message: str


class GoalResponse(BaseSchema):
	title: str | None
	target_amount: int
	current_amount: int


class GoalBody(BaseSchema):
	title: str | None = None
	target_amount: int | None = None


class StopWordResponse(BaseSchema):
	id: int
	word: str


class StopWordBody(BaseSchema):
	word: str


class PassiveIncomeResponse(BaseSchema):
	enabled: bool
	coins_per_interval: int
	interval_minutes: int


class PassiveIncomeBody(BaseSchema):
	enabled: bool | None = None
	coins_per_interval: int | None = None
	interval_minutes: int | None = None
