from __future__ import annotations

from datetime import datetime

from src.schemas.pydantic.common import (
	BaseSchema,
	Paginated,
	PaginationFilters,
)


class UserResponse(BaseSchema):
	id: int
	telegram_id: int
	username: str | None
	display_name: str | None
	avatar_url: str | None
	role: str | None
	balance: int
	created_at: datetime


class UserUpdateBody(BaseSchema):
	display_name: str | None = None
	description: str | None = None


class UserRoleBody(BaseSchema):
	role: str


class UserRoleResponse(BaseSchema):
	id: int
	role: str
	balance: int


class GoalPreview(BaseSchema):
	title: str | None
	target_amount: int
	current_amount: int


class AlertPreview(BaseSchema):
	bg_color: str
	text_color: str
	font: str
	duration_sec: int


class StreamerItemResponse(BaseSchema):
	id: int
	username: str | None
	display_name: str | None
	avatar_url: str | None
	is_live: bool
	goal: GoalPreview | None


class StreamerListResponse(Paginated[StreamerItemResponse]):
	pass


class StreamerProfileResponse(BaseSchema):
	id: int
	username: str | None
	display_name: str | None
	avatar_url: str | None
	description: str | None
	is_live: bool
	goal: GoalPreview | None
	alert_preview: AlertPreview | None


class StreamerFilters(PaginationFilters):
	search: str | None = None
