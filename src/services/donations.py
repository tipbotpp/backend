import asyncio

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.core.configs import cfg
from src.core.exc.exceptions import (
	ForbiddenError,
	InsufficientBalanceError,
	StreamerRequiredError,
	StreamNotActiveError,
	UserNotFoundError,
	ViewerRequiredError,
)
from src.core.storages import S3Manager
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
from src.services.logger import get_logger
from src.services.ml import MLService

logger = get_logger().bind(layer="service", module="donations")


class DonationService:
	def __init__(
		self,
		session: AsyncSession,
		session_factory: async_sessionmaker[AsyncSession],
		ml_service: MLService,
		s3: S3Manager,
	) -> None:
		self._session = session
		self._session_factory = session_factory
		self._ml_service = ml_service
		self._s3 = s3

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
			request_message=message,
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

		if user.balance < amount:
			log.error("insufficient balance", user_balance=user.balance)
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

		if message:
			alert_settings = await sql.alert_settings_repo.get_by_streamer_id(self._session, streamer_id)
			voice = alert_settings.tts_voice if alert_settings else "silero_v3_ru"
			log.debug("tts task scheduled", donation_id=donation.id, voice=voice)
			asyncio.create_task(
				self._process_tts(
					donation_id=donation.id,
					text=message,
					donor_name=user.username or str(user.telegram_id),
					amount=amount,
					voice=voice,
				),
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
		log = logger.bind(
			donation_id=donation_id,
			donor_name=donor_name,
			request_amount=amount,
			voice=voice,
		)
		log.info("tts.process started")
		try:
			result = await self._ml_service.synthesize_tts(
				text=text,
				donor_name=donor_name,
				amount=amount,
				voice=voice,
				donation_id=donation_id,
			)
			audio_url = await self._s3.generate_presigned_url(cfg.s3.aws_bucket, result.audio_key)
			async with self._session_factory.begin() as session:
				await sql.donations_repo.update_ml_artifacts(
					session,
					donation_id,
					audio_url=audio_url,
					status="delivered",
				)
			log.info("tts.process done", audio_key=result.audio_key)
		except Exception as e:
			log.error("tts.process failed", error=str(e))

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
