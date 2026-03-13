import dataclasses

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.donations import Donations
from src.schemas.dataclasses.donations import DonationCreateDTO, DonationDTO
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


async def delete(session: AsyncSession, id: int) -> None:
	instance = await session.get(Donations, id)
	if instance is not None:
		await session.delete(instance)
		await session.flush()
