import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from src.repos.sql import users_repo


@pytest.mark.asyncio
async def test_create_user(session: AsyncSession) -> None:
	user = await users_repo.create(
		session,
		{
			"id": 1,
			"email": "test@test.com",
		},
	)

	assert user.id == 1


@pytest.mark.asyncio
async def test_get_user_by_id(session: AsyncSession) -> None:
	await users_repo.create(
		session,
		{
			"id": 2,
			"email": "get@test.com",
		},
	)

	user = await users_repo.get_by_id(session, 2)

	assert user is not None
	assert user.email == "get@test.com"


@pytest.mark.asyncio
async def test_update_user(session: AsyncSession) -> None:
	await users_repo.create(
		session,
		{
			"id": 3,
			"email": "old@test.com",
		},
	)

	await users_repo.update(
		session,
		3,
		{
			"email": "new@test.com",
		},
	)

	user = await users_repo.get_by_id(session, 3)

	assert user.email == "new@test.com"


@pytest.mark.asyncio
async def test_soft_delete_user(session: AsyncSession) -> None:
	await users_repo.create(
		session,
		{
			"id": 4,
			"email": "delete@test.com",
		},
	)

	await users_repo.delete(session, 4)

	user = await users_repo.get_by_id(session, 4)

	assert user is None
