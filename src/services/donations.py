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


class DonationService:
	def __init__(self, session: AsyncSession) -> None:
		self._session = session

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

		return donation

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
