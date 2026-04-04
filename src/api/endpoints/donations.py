from typing import Annotated

from dishka.integrations.fastapi import DishkaRoute, FromDishka, inject
from fastapi import APIRouter, Depends

from src.di.deps.auth import CurrentUserDep
from src.schemas.pydantic import donations as donations_schema
from src.services.donations import DonationService

router = APIRouter(prefix="/donations", route_class=DishkaRoute)


@router.post("", response_model=donations_schema.DonationCreateResponse, status_code=201)
@inject
async def send_donation(
	body: donations_schema.DonationBody,
	donation_service: FromDishka[DonationService],
	user: CurrentUserDep,
) -> donations_schema.DonationCreateResponse:
	donation = await donation_service.send(
		user=user,
		streamer_id=body.streamer_id,
		amount=body.amount,
		message=body.message,
	)
	return donations_schema.DonationCreateResponse(
		donation_id=donation.id,
		status=donation.status,
		message="Донат отправлен и ожидает обработки",
	)


@router.get("/session", response_model=donations_schema.SessionStatsResponse)
@inject
async def get_session_stats(
	donation_service: FromDishka[DonationService],
	user: CurrentUserDep,
) -> donations_schema.SessionStatsResponse:
	stats = await donation_service.get_session_stats(user)
	return donations_schema.SessionStatsResponse(
		session_id=stats.session_id,
		total_collected=stats.total_collected,
		donations_count=stats.donations_count,
		top_donator=(
			donations_schema.TopDonatorResponse(
				username=stats.top_donator.username,
				total_amount=stats.top_donator.total_amount,
			)
			if stats.top_donator
			else None
		),
		timeline=[
			donations_schema.TimelineItemResponse(time=item.time, amount=item.amount)
			for item in stats.timeline
		],
	)


@router.get("/history", response_model=donations_schema.DonationHistoryResponse)
@inject
async def get_history(
	filters: Annotated[donations_schema.DonationHistoryFilters, Depends()],
	donation_service: FromDishka[DonationService],
	user: CurrentUserDep,
) -> donations_schema.DonationHistoryResponse:
	items, total = await donation_service.get_history(
		user=user,
		type_filter=filters.type,
		limit=filters.limit,
		offset=filters.offset,
	)
	return donations_schema.DonationHistoryResponse(
		items=[
			donations_schema.DonationHistoryItemResponse(
				id=item.id,
				amount=item.amount,
				message=item.message,
				status=item.status,
				from_user=donations_schema.DonorResponse(id=item.from_user.id, username=item.from_user.username),
				to_streamer=donations_schema.DonorResponse(id=item.to_streamer.id, username=item.to_streamer.username),
				created_at=item.created_at,
			)
			for item in items
		],
		total=total,
		limit=filters.limit,
		offset=filters.offset,
	)
