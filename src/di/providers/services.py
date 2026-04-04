from dishka import Provider, Scope, provide
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from src.services.auth import AuthService
from src.services.balance import BalanceService
from src.services.donations import DonationService


class ServiceProvider(Provider):
	scope = Scope.REQUEST

	@provide
	def get_auth_service(self, session: AsyncSession, redis: Redis) -> AuthService:
		return AuthService(session, redis)

	@provide
	def get_balance_service(self, session: AsyncSession) -> BalanceService:
		return BalanceService(session)

	@provide
	def get_donation_service(self, session: AsyncSession) -> DonationService:
		return DonationService(session)
