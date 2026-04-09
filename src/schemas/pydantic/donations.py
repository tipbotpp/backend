from __future__ import annotations

from datetime import datetime

from pydantic import Field

from src.schemas.pydantic.common import (
	BaseSchema,
	Paginated,
	PaginationFilters,
)


class DonationBody(BaseSchema):
	streamer_id: int
	amount: int = Field(gt=0, description="Сумма доната в монетах")
	message: str | None = None


class DonationCreateResponse(BaseSchema):
	donation_id: int
	status: str
	message: str


class DonorResponse(BaseSchema):
	id: int
	username: str | None


class DonationHistoryItemResponse(BaseSchema):
	id: int
	amount: int
	message: str | None
	status: str
	audio_url: str | None
	image_url: str | None
	from_user: DonorResponse
	to_streamer: DonorResponse
	created_at: datetime


class DonationHistoryResponse(Paginated[DonationHistoryItemResponse]):
	pass


class TopDonatorResponse(BaseSchema):
	username: str | None
	total_amount: int


class TimelineItemResponse(BaseSchema):
	time: str
	amount: int


class SessionStatsResponse(BaseSchema):
	session_id: int
	total_collected: int
	donations_count: int
	top_donator: TopDonatorResponse | None
	timeline: list[TimelineItemResponse]


class DonationHistoryFilters(PaginationFilters):
	type: str | None = None
