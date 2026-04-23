import pytest
from src.repos.sql import users_repo


@pytest.mark.asyncio
async def test_db_integrity(session):

    user = await users_repo.create(session, {
        "id": 10,
        "email": "integrity@test.com"
    })

    fetched = await users_repo.get_by_id(session, 10)

    assert fetched.id == user.id
    assert fetched.email == user.email