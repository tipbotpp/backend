import dataclasses

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.balance_transactions import BalanceTransactions
from src.schemas.dataclasses.balance import BalanceTransactionCreateDTO, BalanceTransactionDTO
from src.utils.mappers import map_model


async def get_by_id(session: AsyncSession, id: int) -> BalanceTransactionDTO | None:
	instance = await session.get(BalanceTransactions, id)
	if instance is None:
		return None
	return map_model(instance, BalanceTransactionDTO)


async def get_by_ids(session: AsyncSession, ids: list[int]) -> list[BalanceTransactionDTO]:
	result = await session.execute(select(BalanceTransactions).where(BalanceTransactions.id.in_(ids)))
	return [map_model(row, BalanceTransactionDTO) for row in result.scalars().all()]


async def create(session: AsyncSession, dto: BalanceTransactionCreateDTO) -> BalanceTransactionDTO:
	instance = BalanceTransactions(**dataclasses.asdict(dto))
	session.add(instance)
	await session.flush()
	await session.refresh(instance)
	return map_model(instance, BalanceTransactionDTO)


async def delete(session: AsyncSession, id: int) -> None:
	instance = await session.get(BalanceTransactions, id)
	if instance is not None:
		await session.delete(instance)
		await session.flush()
