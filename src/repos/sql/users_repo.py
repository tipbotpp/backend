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


async def get_by_username(session: AsyncSession, username: str) -> UserDTO | None:
	result = await session.execute(
		select(Users).where(Users.username.ilike(username)),
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


async def update_profile(
	session: AsyncSession,
	telegram_id: int,
	username: str | None,
	display_name: str | None,
	avatar_url: str | None,
) -> UserDTO | None:
	instance = await session.get(Users, telegram_id)
	if instance is None:
		return None
	changed = False
	for field, value in (
		("username", username),
		("display_name", display_name),
		("avatar_url", avatar_url),
	):
		if value is not None and getattr(instance, field) != value:
			setattr(instance, field, value)
			changed = True
	if changed:
		await session.flush()
		await session.refresh(instance)
	return map_model(instance, UserDTO)


async def update_profile_custom(
	session: AsyncSession,
	telegram_id: int,
	display_name: str | None = None,
	description: str | None = None,
) -> UserDTO | None:
	"""Обновление профиля пользователем через API. Если передан display_name — выставляет флаг display_name_custom=True."""
	instance = await session.get(Users, telegram_id)
	if instance is None:
		return None
	changed = False
	if display_name is not None and instance.display_name != display_name:
		instance.display_name = display_name
		instance.display_name_custom = True
		changed = True
	if description is not None and instance.description != description:
		instance.description = description
		changed = True
	if changed:
		await session.flush()
		await session.refresh(instance)
	return map_model(instance, UserDTO)


async def update_balance(session: AsyncSession, telegram_id: int, new_balance: int) -> UserDTO | None:
	instance = await session.get(Users, telegram_id)
	if instance is None:
		return None
	instance.balance = new_balance
	await session.flush()
	await session.refresh(instance)
	return map_model(instance, UserDTO)


async def delete(session: AsyncSession, id: int) -> None:
	instance = await session.get(Users, id)
	if instance is not None:
		await session.delete(instance)
		await session.flush()
