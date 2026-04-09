import httpx
from dishka import Provider, Scope, provide
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.services.auth import AuthService
from src.services.balance import BalanceService
from src.services.donations import DonationService
from src.services.ml import MLService


class ServiceProvider(Provider):
	scope = Scope.REQUEST

	@provide
	def get_auth_service(self, session: AsyncSession, redis: Redis) -> AuthService:
		return AuthService(session, redis)

	@provide
	def get_balance_service(self, session: AsyncSession) -> BalanceService:
		return BalanceService(session)

	@provide
	def get_ml_service(self, client: httpx.AsyncClient) -> MLService:
		return MLService(client)

	@provide
	def get_donation_service(
		self,
		session: AsyncSession,
		session_factory: async_sessionmaker[AsyncSession],
		ml_service: MLService,
	) -> DonationService:
		return DonationService(session, session_factory, ml_service)
