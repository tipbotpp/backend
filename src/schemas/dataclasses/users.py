from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class UserDTO:
	id: int
	telegram_id: int
	username: str | None
	display_name: str | None
	description: str | None
	avatar_url: str | None
	role: str | None
	balance: int
	created_at: datetime
	updated_at: datetime


@dataclass(slots=True)
class UserCreateDTO:
	telegram_id: int
	username: str | None = None
	display_name: str | None = None
	description: str | None = None
	avatar_url: str | None = None
	role: str | None = None
	balance: int = 0


@dataclass(slots=True)
class GoalDTO:
	title: str | None
	target_amount: int
	current_amount: int


@dataclass(slots=True)
class AlertPreviewDTO:
	bg_color: str
	text_color: str
	font: str
	duration_sec: int


@dataclass(slots=True)
class StreamerItemDTO:
	id: int
	username: str | None
	display_name: str | None
	avatar_url: str | None
	is_live: bool
	goal: GoalDTO | None


@dataclass(slots=True)
class StreamerProfileDTO:
	id: int
	username: str | None
	display_name: str | None
	avatar_url: str | None
	description: str | None
	is_live: bool
	goal: GoalDTO | None
	alert_preview: AlertPreviewDTO | None
