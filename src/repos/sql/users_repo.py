from __future__ import annotations

import dataclasses

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.users import Users
from src.schemas.dataclasses.users import UserCreateDTO, UserDTO
from src.utils.mappers import map_model


async def get_by_id(session: AsyncSession, id: int) -> UserDTO | None:
	instance = await session.get(Users, id)
	if instance is None:
		return None
	return map_model(instance, UserDTO)


async def get_by_telegram_id(
	session: AsyncSession,
	telegram_id: int,
) -> UserDTO | None:
	result = await session.execute(
		select(Users).where(Users.telegram_id == telegram_id),
	)
	instance = result.scalar_one_or_none()
	if instance is None:
		return None
	return map_model(instance, UserDTO)


async def get_by_ids(session: AsyncSession, ids: list[int]) -> list[UserDTO]:
	result = await session.execute(
		select(Users).where(Users.telegram_id.in_(ids)),
	)
	return [map_model(row, UserDTO) for row in result.scalars().all()]


async def create(session: AsyncSession, dto: UserCreateDTO) -> UserDTO:
	instance = Users(**dataclasses.asdict(dto))
	session.add(instance)
	await session.flush()
	await session.refresh(instance)
	return map_model(instance, UserDTO)


async def update_role(
	session: AsyncSession,
	telegram_id: int,
	role: str,
	balance: int | None = None,
) -> UserDTO | None:
	instance = await session.get(Users, telegram_id)
	if instance is None:
		return None
	instance.role = role
	if balance is not None:
		instance.balance = balance
	await session.flush()
	await session.refresh(instance)
	return map_model(instance, UserDTO)


async def delete(session: AsyncSession, id: int) -> None:
	instance = await session.get(Users, id)
	if instance is not None:
		await session.delete(instance)
		await session.flush()
