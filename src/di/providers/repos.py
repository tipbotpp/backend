from collections.abc import AsyncGenerator

from dishka import Provider, Scope, provide
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


class RepositoryProvider(Provider):
	scope = Scope.REQUEST

	@provide
	async def get_session(
		self,
		factory: async_sessionmaker[AsyncSession],
	) -> AsyncGenerator[AsyncSession, None]:
		async with factory() as session:
			async with session.begin():
				yield session
