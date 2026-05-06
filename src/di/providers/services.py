import httpx
from arq.connections import ArqRedis
from dishka import Provider, Scope, provide
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from src.services.auth import AuthService
from src.services.balance import BalanceService
from src.services.donations import DonationService
from src.services.ml import MLService
from src.services.settings import SettingsService
from src.services.stream import StreamService


class ServiceProvider(Provider):
	scope = Scope.REQUEST

	@provide
	def get_auth_service(
		self,
		session: AsyncSession,
		redis: Redis,
	) -> AuthService:
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
		ml_service: MLService,
		arq_pool: ArqRedis,
	) -> DonationService:
		return DonationService(session, ml_service, arq_pool)

	@provide
	def get_stream_service(self, session: AsyncSession) -> StreamService:
		return StreamService(session)

	@provide
	def get_settings_service(
		self,
		session: AsyncSession,
		redis: Redis,
	) -> SettingsService:
		return SettingsService(session, redis)
