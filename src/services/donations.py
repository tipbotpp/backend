from arq.connections import ArqRedis
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exc.exceptions import (
	ForbiddenError,
	InsufficientBalanceError,
	StreamerRequiredError,
	StreamNotActiveError,
	UserNotFoundError,
	ViewerRequiredError,
)
from src.repos import sql
from src.repos.redis import ws_queue_repo
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
from src.services.logger import get_logger
from src.services.ml import MLService

logger = get_logger().bind(layer="service", module="donations")


class DonationService:
	def __init__(
		self,
		session: AsyncSession,
		ml_service: MLService,
		arq_pool: ArqRedis,
	) -> None:
		self._session = session
		self._ml_service = ml_service
		self._arq_pool = arq_pool

	async def send(
		self,
		user: UserDTO,
		streamer_id: int,
		amount: int,
		message: str | None,
	) -> DonationDTO:
		log = logger.bind(
			request_user_id=user.telegram_id,
			request_streamer_id=streamer_id,
			request_amount=amount,
			request_message_length=len(message) if message else 0,
		)
		log.info("donation.send started")

		if user.role != UserRole.VIEWER:
			log.error("viewer role required", user_role=user.role)
			raise ViewerRequiredError()

		if user.telegram_id == streamer_id:
			log.error("user cannot donate to themselves")
			raise ForbiddenError()

		streamer = await sql.users_repo.get_by_telegram_id(self._session, streamer_id)
		if streamer is None or streamer.role != UserRole.STREAMER:
			log.error("streamer not found")
			raise UserNotFoundError()

		stream_session = await sql.stream_sessions_repo.get_active_by_streamer_id(self._session, streamer_id)
		if stream_session is None:
			log.error("stream not active")
			raise StreamNotActiveError()

		# Быстрый фейл на стейл-данных — не ходим в БД если баланс заведомо мал
		if user.balance < amount:
			log.error("insufficient balance (stale check)", user_balance=user.balance)
			raise InsufficientBalanceError()

		if message:
			stop_words = await sql.stop_words_repo.get_by_streamer_id(self._session, streamer_id)
			log.debug("moderation started", stop_words_count=len(stop_words))
			await self._ml_service.moderate(
				text=message,
				stopwords=[sw.word for sw in stop_words],
				streamer_id=streamer_id,
			)
			log.debug("moderation passed")

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
		log.info("donation created", donation_id=donation.id)

		# Атомарный декремент: списываем только если balance >= amount прямо сейчас
		new_viewer_balance = await sql.users_repo.decrement_balance(
			self._session, user.telegram_id, amount,
		)
		if new_viewer_balance is None:
			log.error("insufficient balance (atomic check)", user_balance=user.balance)
			raise InsufficientBalanceError()

		await sql.balance_transactions_repo.create(
			self._session,
			BalanceTransactionCreateDTO(
				user_id=user.telegram_id,
				amount=-amount,
				type=BalanceTransactionType.DONATION_SENT,
				ref_donation_id=donation.id,
			),
		)

		await sql.users_repo.increment_balance(self._session, streamer_id, amount)
		await sql.balance_transactions_repo.create(
			self._session,
			BalanceTransactionCreateDTO(
				user_id=streamer_id,
				amount=amount,
				type=BalanceTransactionType.DONATION_RECEIVED,
				ref_donation_id=donation.id,
			),
		)

		alert_settings = await sql.alert_settings_repo.get_by_streamer_id(self._session, streamer_id)
		tts_enabled = bool(message) and (alert_settings.tts_enabled if alert_settings else True)
		image_enabled = bool(message) and (alert_settings.image_enabled if alert_settings else True)
		voice = alert_settings.tts_voice if alert_settings else "silero_v3_ru"

		job = await self._arq_pool.enqueue_job(
			"process_donation_media",
			donation_id=donation.id,
			text=message,
			donor_name=user.username or str(user.telegram_id),
			amount=amount,
			voice=voice,
			tts_enabled=tts_enabled,
			image_enabled=image_enabled,
			streamer_id=streamer_id,
			stream_token=stream_session.stream_token,
			alert_bg_color=alert_settings.bg_color if alert_settings else "#1a1a2e",
			alert_text_color=alert_settings.text_color if alert_settings else "#ffffff",
			alert_font=alert_settings.font if alert_settings else "Roboto",
			alert_duration_sec=alert_settings.duration_sec if alert_settings else 5,
		)
		if job is not None:
			await ws_queue_repo.push_job_id(self._arq_pool, stream_session.stream_token, job.job_id)
		log.info("donation.send done — media task enqueued", donation_id=donation.id)

		return donation

	async def get_history(
		self,
		user: UserDTO,
		type_filter: str | None,
		limit: int,
		offset: int,
	) -> tuple[list[DonationWithUsersDTO], int]:
		log = logger.bind(
			request_user_id=user.telegram_id,
			request_type_filter=type_filter,
			request_limit=limit,
			request_offset=offset,
		)
		log.debug("donation.get_history started")
		result = await sql.donations_repo.get_history(
			self._session,
			user.telegram_id,
			type_filter,
			limit,
			offset,
		)
		log.debug("donation.get_history done", count=result[1])
		return result

	async def get_session_stats(self, user: UserDTO) -> SessionStatsDTO:
		log = logger.bind(request_user_id=user.telegram_id)
		log.debug("donation.get_session_stats started")

		if user.role != UserRole.STREAMER:
			log.error("streamer role required", user_role=user.role)
			raise StreamerRequiredError()

		stream_session = await sql.stream_sessions_repo.get_active_by_streamer_id(self._session, user.telegram_id)
		if stream_session is None:
			log.error("no active stream session")
			raise StreamNotActiveError()

		stats = await sql.donations_repo.get_session_stats(self._session, stream_session.id)
		log.debug("donation.get_session_stats done", session_id=stream_session.id)
		return stats
