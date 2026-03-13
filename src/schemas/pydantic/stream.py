from __future__ import annotations

from datetime import datetime

from src.schemas.pydantic.common import BaseSchema


class StreamStartBody(BaseSchema):
	passive_income_enabled: bool = False


class StreamStartResponse(BaseSchema):
	session_id: int
	widget_url: str
	ws_url: str
	stream_token: str
	started_at: datetime


class StreamStopResponse(BaseSchema):
	session_id: int
	total_collected: int
	donations_count: int
	duration_seconds: int
	ended_at: datetime


class StreamStatusResponse(BaseSchema):
	is_live: bool
	session_id: int | None
	started_at: datetime | None
	widget_url: str | None
