from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class AlertSettingsCreateDTO:
	streamer_id: int
	bg_color: str = "#1a1a2e"
	text_color: str = "#ffffff"
	font: str = "Roboto"
	duration_sec: int = 5
	image_enabled: bool = True
	tts_enabled: bool = True
	tts_voice: str = "silero_v3_ru"


@dataclass(slots=True)
class StreamGoalCreateDTO:
	streamer_id: int
	title: str | None = None
	target_amount: int = 0
	current_amount: int = 0


@dataclass(slots=True)
class StopWordCreateDTO:
	streamer_id: int
	word: str


@dataclass(slots=True)
class PassiveIncomeSettingsCreateDTO:
	streamer_id: int
	enabled: bool = False
	coins_per_interval: int = 10
	interval_minutes: int = 5


@dataclass(slots=True)
class AlertSettingsDTO:
	id: int
	streamer_id: int
	bg_color: str
	text_color: str
	font: str
	duration_sec: int
	image_enabled: bool
	tts_enabled: bool
	tts_voice: str


@dataclass(slots=True)
class StreamGoalDTO:
	id: int
	streamer_id: int
	title: str | None
	target_amount: int
	current_amount: int


@dataclass(slots=True)
class StopWordDTO:
	id: int
	streamer_id: int
	word: str


@dataclass(slots=True)
class PassiveIncomeSettingsDTO:
	id: int
	streamer_id: int
	enabled: bool
	coins_per_interval: int
	interval_minutes: int
