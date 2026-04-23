import pytest
import asyncio

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from src.models import Base
from src.core.db import get_session


TEST_DB_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(TEST_DB_URL, echo=False)
TestingSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


# event loop for pytest-asyncio
@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# create tables once
@pytest.fixture(scope="session")
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


# DB session per test
@pytest.fixture
async def session(setup_db):
    async with TestingSessionLocal() as session:
        yield session
        await session.rollback()