from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base
from src.utils import local_time


class BalanceTransactions(Base):
	__tablename__ = "balance_transactions"

	id: Mapped[int] = mapped_column(
		BigInteger,
		primary_key=True,
		autoincrement=True,
		comment="ID транзакции",
	)
	user_id: Mapped[int] = mapped_column(
		BigInteger,
		ForeignKey("users.telegram_id"),
		nullable=False,
		comment="ID пользователя, которому принадлежит транзакция",
	)
	amount: Mapped[int] = mapped_column(
		BigInteger,
		nullable=False,
		comment="Сумма транзакции в монетах (отрицательная при списании)",
	)
	type: Mapped[str] = mapped_column(
		String(32),
		nullable=False,
		comment="Тип транзакции: topup | donation_sent | donation_received | passive_income | initial",
	)
	ref_donation_id: Mapped[int | None] = mapped_column(
		BigInteger,
		ForeignKey("donations.id"),
		nullable=True,
		default=None,
		comment="ID доната, с которым связана транзакция (если применимо)",
	)
	created_at: Mapped[datetime] = mapped_column(
		DateTime(timezone=True),
		nullable=False,
		default=local_time.now,
		server_default=func.now(),
		comment="Дата и время создания транзакции",
	)
