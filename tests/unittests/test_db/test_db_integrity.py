import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from src.repos.sql import users_repo


@pytest.mark.asyncio
async def test_db_integrity(session: AsyncSession) -> None:
	user = await users_repo.create(
		session,
		{
			"id": 10,
			"email": "integrity@test.com",
		},
	)

	assert user.id == 10
