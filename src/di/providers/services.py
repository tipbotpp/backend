from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from dishka import Provider, Scope, provide

from src.services.auth import AuthService
from src.services.balance import BalanceService


class ServiceProvider(Provider):
	scope = Scope.REQUEST

	@provide
	def get_auth_service(self, session: AsyncSession, redis: Redis) -> AuthService:
		return AuthService(session, redis)

	@provide
	def get_balance_service(self, session: AsyncSession) -> BalanceService:
		return BalanceService(session)
