import dataclasses

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.stream_sessions import StreamSessions
from src.schemas.dataclasses.streams import (
	StreamSessionCreateDTO,
	StreamSessionDTO,
)
from src.utils.mappers import map_model


async def get_by_id(session: AsyncSession, id: int) -> StreamSessionDTO | None:
	instance = await session.get(StreamSessions, id)
	if instance is None:
		return None
	return map_model(instance, StreamSessionDTO)


async def get_by_ids(session: AsyncSession, ids: list[int]) -> list[StreamSessionDTO]:
	result = await session.execute(select(StreamSessions).where(StreamSessions.id.in_(ids)))
	return [map_model(row, StreamSessionDTO) for row in result.scalars().all()]


async def create(session: AsyncSession, dto: StreamSessionCreateDTO) -> StreamSessionDTO:
	instance = StreamSessions(**dataclasses.asdict(dto))
	session.add(instance)
	await session.flush()
	await session.refresh(instance)
	return map_model(instance, StreamSessionDTO)


async def get_active_by_streamer_id(session: AsyncSession, streamer_id: int) -> StreamSessionDTO | None:
	result = await session.execute(
		select(StreamSessions).where(
			StreamSessions.streamer_id == streamer_id,
			StreamSessions.is_active.is_(True),
		),
	)
	instance = result.scalar_one_or_none()
	if instance is None:
		return None
	return map_model(instance, StreamSessionDTO)


async def delete(session: AsyncSession, id: int) -> None:
	instance = await session.get(StreamSessions, id)
	if instance is not None:
		await session.delete(instance)
		await session.flush()
