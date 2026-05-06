from __future__ import annotations

import dataclasses

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.stream_sessions import StreamSessions
from src.models.users import Users
from src.schemas.dataclasses.users import UserCreateDTO, UserDTO
from src.schemas.enums.users import UserRole
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


async def get_by_username(
	session: AsyncSession,
	username: str,
) -> UserDTO | None:
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


async def update_balance(
	session: AsyncSession,
	telegram_id: int,
	new_balance: int,
) -> UserDTO | None:
	instance = await session.get(Users, telegram_id)
	if instance is None:
		return None
	instance.balance = new_balance
	await session.flush()
	await session.refresh(instance)
	return map_model(instance, UserDTO)


async def increment_balance(
	session: AsyncSession,
	telegram_id: int,
	amount: int,
) -> int | None:
	"""Атомарно прибавляет amount к балансу. Возвращает новый баланс или None если юзер не найден."""
	result = await session.execute(
		update(Users)
		.where(Users.telegram_id == telegram_id)
		.values(balance=Users.balance + amount)
		.returning(Users.balance),
	)
	return result.scalar_one_or_none()


async def decrement_balance(
	session: AsyncSession,
	telegram_id: int,
	amount: int,
) -> int | None:
	"""Атомарно вычитает amount из баланса только если баланс >= amount.
	Возвращает новый баланс при успехе или None если баланса недостаточно / юзер не найден."""
	result = await session.execute(
		update(Users)
		.where(Users.telegram_id == telegram_id, Users.balance >= amount)
		.values(balance=Users.balance - amount)
		.returning(Users.balance),
	)
	return result.scalar_one_or_none()


async def get_active_streamers(
	session: AsyncSession,
	search: str | None = None,
	limit: int = 20,
	offset: int = 0,
) -> tuple[list[UserDTO], int]:
	"""Стримеры с активной сессией. Возвращает (items, total)."""
	base = (
		select(Users)
		.join(StreamSessions, StreamSessions.streamer_id == Users.telegram_id)
		.where(
			Users.role == UserRole.STREAMER,
			StreamSessions.is_active.is_(True),
		)
		.distinct()
	)
	if search:
		pattern = f"%{search}%"
		base = base.where(
			Users.username.ilike(pattern) | Users.display_name.ilike(pattern),
		)

	total_result = await session.execute(
		select(func.count()).select_from(base.subquery()),
	)
	total = total_result.scalar_one()

	result = await session.execute(base.limit(limit).offset(offset))
	return [map_model(row, UserDTO) for row in result.scalars().all()], total


async def get_all_viewers(session: AsyncSession) -> list[UserDTO]:
	result = await session.execute(
		select(Users).where(Users.role == UserRole.VIEWER),
	)
	return [map_model(row, UserDTO) for row in result.scalars().all()]


async def delete(session: AsyncSession, id: int) -> None:
	instance = await session.get(Users, id)
	if instance is not None:
		await session.delete(instance)
		await session.flush()
