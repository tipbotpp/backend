from sqlalchemy import BigInteger, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base


class StreamGoals(Base):
	__tablename__ = "stream_goals"

	id: Mapped[int] = mapped_column(
		BigInteger,
		primary_key=True,
		autoincrement=True,
		comment="ID цели стрима",
	)
	streamer_id: Mapped[int] = mapped_column(
		BigInteger,
		ForeignKey("users.telegram_id"),
		unique=True,
		nullable=False,
		comment="ID стримера, которому принадлежит цель",
	)
	title: Mapped[str | None] = mapped_column(
		String(256),
		nullable=True,
		default=None,
		comment="Название цели стрима",
	)
	target_amount: Mapped[int] = mapped_column(
		BigInteger,
		nullable=False,
		default=0,
		server_default="0",
		comment="Целевая сумма в монетах",
	)
	current_amount: Mapped[int] = mapped_column(
		BigInteger,
		nullable=False,
		default=0,
		server_default="0",
		comment="Текущая набранная сумма в монетах",
	)
