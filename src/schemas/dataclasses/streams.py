from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class StreamSessionCreateDTO:
	streamer_id: int
	stream_token: str
	is_active: bool = True
	passive_income_enabled: bool = False


@dataclass(slots=True)
class StreamSessionDTO:
	id: int
	streamer_id: int
	stream_token: str
	is_active: bool
	passive_income_enabled: bool
	started_at: datetime
	ended_at: datetime | None
