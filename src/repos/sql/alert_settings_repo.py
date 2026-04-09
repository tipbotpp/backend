import dataclasses

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.alert_settings import AlertSettings
from src.schemas.dataclasses.settings import (
	AlertSettingsCreateDTO,
	AlertSettingsDTO,
)
from src.utils.mappers import map_model


async def get_by_streamer_id(session: AsyncSession, streamer_id: int) -> AlertSettingsDTO | None:
	result = await session.execute(select(AlertSettings).where(AlertSettings.streamer_id == streamer_id))
	instance = result.scalar_one_or_none()
	if instance is None:
		return None
	return map_model(instance, AlertSettingsDTO)


async def get_by_id(session: AsyncSession, id: int) -> AlertSettingsDTO | None:
	instance = await session.get(AlertSettings, id)
	if instance is None:
		return None
	return map_model(instance, AlertSettingsDTO)


async def get_by_ids(session: AsyncSession, ids: list[int]) -> list[AlertSettingsDTO]:
	result = await session.execute(select(AlertSettings).where(AlertSettings.id.in_(ids)))
	return [map_model(row, AlertSettingsDTO) for row in result.scalars().all()]


async def create(session: AsyncSession, dto: AlertSettingsCreateDTO) -> AlertSettingsDTO:
	instance = AlertSettings(**dataclasses.asdict(dto))
	session.add(instance)
	await session.flush()
	await session.refresh(instance)
	return map_model(instance, AlertSettingsDTO)


async def delete(session: AsyncSession, id: int) -> None:
	instance = await session.get(AlertSettings, id)
	if instance is not None:
		await session.delete(instance)
		await session.flush()
