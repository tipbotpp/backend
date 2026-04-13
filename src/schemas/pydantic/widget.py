from __future__ import annotations

from src.schemas.pydantic.common import BaseSchema


class WidgetStreamerSchema(BaseSchema):
	username: str | None
	display_name: str | None


class WidgetAlertStyleSchema(BaseSchema):
	bg_color: str
	text_color: str
	font: str
	duration_sec: int


class WidgetResponse(BaseSchema):
	stream_token: str
	streamer: WidgetStreamerSchema
	alert_style: WidgetAlertStyleSchema
	ws_url: str
