from sqlalchemy.ext.asyncio import AsyncSession

from src.repos import sql
from src.schemas.dataclasses.balance import BalanceTransactionCreateDTO
from src.schemas.dataclasses.users import UserDTO
from src.schemas.enums.balance import BalanceTransactionType


class BalanceService:
	def __init__(self, session: AsyncSession) -> None:
		self._session = session

	async def topup(self, user: UserDTO, amount: int) -> tuple[int, int]:
		"""Пополняет баланс пользователя и записывает транзакцию.

		Возвращает (previous_balance, new_balance).
		"""
		previous_balance = user.balance
		new_balance = previous_balance + amount

		await sql.users_repo.update_balance(self._session, user.telegram_id, new_balance)
		await sql.balance_transactions_repo.create(
			self._session,
			BalanceTransactionCreateDTO(
				user_id=user.telegram_id,
				amount=amount,
				type=BalanceTransactionType.TOPUP,
			),
		)

		return previous_balance, new_balance
