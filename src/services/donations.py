import asyncio
import logging

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.core.exc.exceptions import (
	ForbiddenError,
	InsufficientBalanceError,
	StreamerRequiredError,
	StreamNotActiveError,
	UserNotFoundError,
	ViewerRequiredError,
)
from src.repos import sql
from src.schemas.dataclasses.balance import BalanceTransactionCreateDTO
from src.schemas.dataclasses.donations import (
	DonationCreateDTO,
	DonationDTO,
	DonationWithUsersDTO,
	SessionStatsDTO,
)
from src.schemas.dataclasses.users import UserDTO
from src.schemas.enums.balance import BalanceTransactionType
from src.schemas.enums.users import UserRole
from src.services.ml import MLService

logger = logging.getLogger(__name__)


class DonationService:
	def __init__(
		self,
		session: AsyncSession,
		session_factory: async_sessionmaker[AsyncSession],
		ml_service: MLService,
	) -> None:
		self._session = session
		self._session_factory = session_factory
		self._ml_service = ml_service

	async def send(
		self,
		user: UserDTO,
		streamer_id: int,
		amount: int,
		message: str | None,
	) -> DonationDTO:
		if user.role != UserRole.VIEWER:
			raise ViewerRequiredError()

		if user.telegram_id == streamer_id:
			raise ForbiddenError()

		streamer = await sql.users_repo.get_by_telegram_id(self._session, streamer_id)
		if streamer is None or streamer.role != UserRole.STREAMER:
			raise UserNotFoundError()

		stream_session = await sql.stream_sessions_repo.get_active_by_streamer_id(self._session, streamer_id)
		if stream_session is None:
			raise StreamNotActiveError()

		if user.balance < amount:
			raise InsufficientBalanceError()

		# Модерация — блокирует создание доната если текст нарушает правила
		if message:
			stop_words = await sql.stop_words_repo.get_by_streamer_id(self._session, streamer_id)
			await self._ml_service.moderate(
				text=message,
				stopwords=[sw.word for sw in stop_words],
				streamer_id=streamer_id,
			)

		donation = await sql.donations_repo.create(
			self._session,
			DonationCreateDTO(
				from_user_id=user.telegram_id,
				to_streamer_id=streamer_id,
				session_id=stream_session.id,
				amount=amount,
				message=message,
				status="processing",
			),
		)

		await sql.users_repo.update_balance(self._session, user.telegram_id, user.balance - amount)
		await sql.balance_transactions_repo.create(
			self._session,
			BalanceTransactionCreateDTO(
				user_id=user.telegram_id,
				amount=-amount,
				type=BalanceTransactionType.DONATION_SENT,
				ref_donation_id=donation.id,
			),
		)

		await sql.users_repo.update_balance(self._session, streamer_id, streamer.balance + amount)
		await sql.balance_transactions_repo.create(
			self._session,
			BalanceTransactionCreateDTO(
				user_id=streamer_id,
				amount=amount,
				type=BalanceTransactionType.DONATION_RECEIVED,
				ref_donation_id=donation.id,
			),
		)

		# TTS запускается фоново — не блокирует ответ клиенту
		if message:
			alert_settings = await sql.alert_settings_repo.get_by_streamer_id(self._session, streamer_id)
			voice = alert_settings.tts_voice if alert_settings else "silero_v3_ru"
			asyncio.create_task(
				self._process_tts(
					donation_id=donation.id,
					text=message,
					donor_name=user.username or str(user.telegram_id),
					amount=amount,
					voice=voice,
				)
			)

		return donation

	async def _process_tts(
		self,
		donation_id: int,
		text: str,
		donor_name: str,
		amount: int,
		voice: str,
	) -> None:
		try:
			result = await self._ml_service.synthesize_tts(
				text=text,
				donor_name=donor_name,
				amount=amount,
				voice=voice,
				donation_id=donation_id,
			)
			async with self._session_factory.begin() as session:
				await sql.donations_repo.update_ml_artifacts(
					session,
					donation_id,
					audio_url=result.audio_url,
					status="delivered",
				)
		except Exception:
			logger.exception("TTS failed for donation %d", donation_id)

	async def get_history(
		self,
		user: UserDTO,
		type_filter: str | None,
		limit: int,
		offset: int,
	) -> tuple[list[DonationWithUsersDTO], int]:
		return await sql.donations_repo.get_history(
			self._session,
			user.telegram_id,
			type_filter,
			limit,
			offset,
		)

	async def get_session_stats(self, user: UserDTO) -> SessionStatsDTO:
		if user.role != UserRole.STREAMER:
			raise StreamerRequiredError()

		stream_session = await sql.stream_sessions_repo.get_active_by_streamer_id(self._session, user.telegram_id)
		if stream_session is None:
			raise StreamNotActiveError()

		return await sql.donations_repo.get_session_stats(self._session, stream_session.id)
