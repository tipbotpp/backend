import dataclasses

from sqlalchemy import select
from sqlalchemy import update as sa_update
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.stream_goals import StreamGoals
from src.schemas.dataclasses.settings import StreamGoalCreateDTO, StreamGoalDTO
from src.utils.mappers import map_model


async def get_by_streamer_id(session: AsyncSession, streamer_id: int) -> StreamGoalDTO | None:
	result = await session.execute(
		select(StreamGoals).where(StreamGoals.streamer_id == streamer_id),
	)
	instance = result.scalar_one_or_none()
	if instance is None:
		return None
	return map_model(instance, StreamGoalDTO)


async def get_by_id(session: AsyncSession, id: int) -> StreamGoalDTO | None:
	instance = await session.get(StreamGoals, id)
	if instance is None:
		return None
	return map_model(instance, StreamGoalDTO)


async def get_by_ids(session: AsyncSession, ids: list[int]) -> list[StreamGoalDTO]:
	result = await session.execute(select(StreamGoals).where(StreamGoals.id.in_(ids)))
	return [map_model(row, StreamGoalDTO) for row in result.scalars().all()]


async def create(session: AsyncSession, dto: StreamGoalCreateDTO) -> StreamGoalDTO:
	instance = StreamGoals(**dataclasses.asdict(dto))
	session.add(instance)
	await session.flush()
	await session.refresh(instance)
	return map_model(instance, StreamGoalDTO)


async def update(
	session: AsyncSession,
	streamer_id: int,
	**fields: object,
) -> StreamGoalDTO | None:
	result = await session.execute(select(StreamGoals).where(StreamGoals.streamer_id == streamer_id))
	instance = result.scalar_one_or_none()
	if instance is None:
		return None
	for key, value in fields.items():
		if value is not None and hasattr(instance, key):
			setattr(instance, key, value)
	await session.flush()
	await session.refresh(instance)
	return map_model(instance, StreamGoalDTO)


async def increment_current_amount(session: AsyncSession, streamer_id: int, amount: int) -> None:
	await session.execute(
		sa_update(StreamGoals)
		.where(StreamGoals.streamer_id == streamer_id)
		.values(current_amount=StreamGoals.current_amount + amount),
	)


async def delete(session: AsyncSession, id: int) -> None:
	instance = await session.get(StreamGoals, id)
	if instance is not None:
		await session.delete(instance)
		await session.flush()
