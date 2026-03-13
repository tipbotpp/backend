import dataclasses

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.stream_goals import StreamGoals
from src.schemas.dataclasses.settings import StreamGoalCreateDTO, StreamGoalDTO
from src.utils.mappers import map_model


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


async def delete(session: AsyncSession, id: int) -> None:
	instance = await session.get(StreamGoals, id)
	if instance is not None:
		await session.delete(instance)
		await session.flush()
