import dataclasses

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.passive_income_settings import PassiveIncomeSettings
from src.schemas.dataclasses.settings import PassiveIncomeSettingsCreateDTO, PassiveIncomeSettingsDTO
from src.utils.mappers import map_model


async def get_by_id(session: AsyncSession, id: int) -> PassiveIncomeSettingsDTO | None:
	instance = await session.get(PassiveIncomeSettings, id)
	if instance is None:
		return None
	return map_model(instance, PassiveIncomeSettingsDTO)


async def get_by_ids(session: AsyncSession, ids: list[int]) -> list[PassiveIncomeSettingsDTO]:
	result = await session.execute(select(PassiveIncomeSettings).where(PassiveIncomeSettings.id.in_(ids)))
	return [map_model(row, PassiveIncomeSettingsDTO) for row in result.scalars().all()]


async def create(session: AsyncSession, dto: PassiveIncomeSettingsCreateDTO) -> PassiveIncomeSettingsDTO:
	instance = PassiveIncomeSettings(**dataclasses.asdict(dto))
	session.add(instance)
	await session.flush()
	await session.refresh(instance)
	return map_model(instance, PassiveIncomeSettingsDTO)


async def delete(session: AsyncSession, id: int) -> None:
	instance = await session.get(PassiveIncomeSettings, id)
	if instance is not None:
		await session.delete(instance)
		await session.flush()
