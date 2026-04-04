import dataclasses
from collections import defaultdict

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from src.models.donations import Donations
from src.models.users import Users
from src.schemas.dataclasses.donations import (
	DonationCreateDTO,
	DonationDTO,
	DonationWithUsersDTO,
	DonorDTO,
	SessionStatsDTO,
	TimelineItemDTO,
	TopDonatorDTO,
)
from src.utils.mappers import map_model


async def get_by_id(session: AsyncSession, id: int) -> DonationDTO | None:
	instance = await session.get(Donations, id)
	if instance is None:
		return None
	return map_model(instance, DonationDTO)


async def get_by_ids(session: AsyncSession, ids: list[int]) -> list[DonationDTO]:
	result = await session.execute(select(Donations).where(Donations.id.in_(ids)))
	return [map_model(row, DonationDTO) for row in result.scalars().all()]


async def create(session: AsyncSession, dto: DonationCreateDTO) -> DonationDTO:
	instance = Donations(**dataclasses.asdict(dto))
	session.add(instance)
	await session.flush()
	await session.refresh(instance)
	return map_model(instance, DonationDTO)


async def get_history(
	session: AsyncSession,
	user_id: int,
	type_filter: str | None,
	limit: int,
	offset: int,
) -> tuple[list[DonationWithUsersDTO], int]:
	FromUser = aliased(Users)
	ToStreamer = aliased(Users)

	if type_filter == "sent":
		condition = Donations.from_user_id == user_id
	elif type_filter == "received":
		condition = Donations.to_streamer_id == user_id
	else:
		condition = or_(Donations.from_user_id == user_id, Donations.to_streamer_id == user_id)

	total_result = await session.execute(
		select(func.count()).select_from(Donations).where(condition),
	)
	total = total_result.scalar_one()

	rows = await session.execute(
		select(Donations, FromUser, ToStreamer)
		.join(FromUser, Donations.from_user_id == FromUser.telegram_id)
		.join(ToStreamer, Donations.to_streamer_id == ToStreamer.telegram_id)
		.where(condition)
		.order_by(Donations.created_at.desc())
		.offset(offset)
		.limit(limit),
	)

	items = [
		DonationWithUsersDTO(
			id=donation.id,
			amount=donation.amount,
			message=donation.message,
			status=donation.status,
			from_user=DonorDTO(id=from_user.telegram_id, username=from_user.username),
			to_streamer=DonorDTO(id=to_streamer.telegram_id, username=to_streamer.username),
			created_at=donation.created_at,
		)
		for donation, from_user, to_streamer in rows.tuples().all()
	]

	return items, total


async def get_session_stats(session: AsyncSession, session_id: int) -> SessionStatsDTO:
	agg = await session.execute(
		select(
			func.coalesce(func.sum(Donations.amount), 0).label("total"),
			func.count(Donations.id).label("cnt"),
		).where(Donations.session_id == session_id),
	)
	agg_row = agg.one()

	FromUser = aliased(Users)
	top_row = await session.execute(
		select(FromUser.username, func.sum(Donations.amount).label("total"))
		.join(FromUser, Donations.from_user_id == FromUser.telegram_id)
		.where(Donations.session_id == session_id)
		.group_by(FromUser.telegram_id, FromUser.username)
		.order_by(func.sum(Donations.amount).desc())
		.limit(1),
	)
	top = top_row.one_or_none()
	top_donator = TopDonatorDTO(username=top.username, total_amount=top.total) if top else None

	timeline_rows = await session.execute(
		select(Donations.created_at, Donations.amount)
		.where(Donations.session_id == session_id)
		.order_by(Donations.created_at),
	)
	buckets: dict[str, int] = defaultdict(int)
	for ts, amount in timeline_rows.all():
		minute_bucket = (ts.minute // 15) * 15
		buckets[f"{ts.hour:02d}:{minute_bucket:02d}"] += amount
	timeline = [TimelineItemDTO(time=t, amount=a) for t, a in sorted(buckets.items())]

	return SessionStatsDTO(
		session_id=session_id,
		total_collected=int(agg_row.total),
		donations_count=agg_row.cnt,
		top_donator=top_donator,
		timeline=timeline,
	)


async def delete(session: AsyncSession, id: int) -> None:
	instance = await session.get(Donations, id)
	if instance is not None:
		await session.delete(instance)
		await session.flush()
