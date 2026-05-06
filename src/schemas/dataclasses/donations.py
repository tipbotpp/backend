from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class DonationCreateDTO:
	from_user_id: int
	to_streamer_id: int
	session_id: int
	amount: int
	status: str
	message: str | None = None
	reject_reason: str | None = None
	audio_url: str | None = None
	image_url: str | None = None


@dataclass(slots=True)
class DonationDTO:
	id: int
	from_user_id: int
	to_streamer_id: int
	session_id: int
	amount: int
	message: str | None
	status: str
	reject_reason: str | None
	audio_url: str | None
	image_url: str | None
	created_at: datetime


@dataclass(slots=True)
class DonorDTO:
	id: int
	username: str | None


@dataclass(slots=True)
class DonationWithUsersDTO:
	id: int
	amount: int
	message: str | None
	status: str
	audio_key: str | None
	image_key: str | None
	from_user: DonorDTO
	to_streamer: DonorDTO
	created_at: datetime


@dataclass(slots=True)
class TopDonatorDTO:
	username: str | None
	total_amount: int


@dataclass(slots=True)
class TimelineItemDTO:
	time: str
	amount: int


@dataclass(slots=True)
class DonationMediaResultDTO:
	"""Результат arq-таски process_donation_media.

	Содержит raw S3 ключи — FastAPI WS handler сам генерирует presigned URLs.
	"""
	donation_id: int
	donor_name: str
	amount: int
	message: str | None
	streamer_id: int
	audio_key: str | None
	image_key: str | None
	alert_bg_color: str
	alert_text_color: str
	alert_font: str
	alert_duration_sec: int


@dataclass(slots=True)
class SessionStatsDTO:
	session_id: int
	total_collected: int
	donations_count: int
	top_donator: TopDonatorDTO | None
	timeline: list[TimelineItemDTO]
