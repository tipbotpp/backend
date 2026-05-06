import asyncio
from collections.abc import AsyncGenerator, Generator

import pytest
from sqlalchemy.ext.asyncio import (
	AsyncSession,
	async_sessionmaker,
	create_async_engine,
)
from src.models import Base

DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(DATABASE_URL, echo=False)
TestingSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
	loop = asyncio.new_event_loop()
	yield loop
	loop.close()


@pytest.fixture(scope="session")
async def setup_db() -> None:
	async with engine.begin() as conn:
		await conn.run_sync(Base.metadata.create_all)


@pytest.fixture
async def session(setup_db: None) -> AsyncGenerator[AsyncSession, None]:
	async with TestingSessionLocal() as session:
		yield session
