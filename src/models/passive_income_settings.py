from sqlalchemy import BigInteger, Boolean, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base


class PassiveIncomeSettings(Base):
	__tablename__ = "passive_income_settings"

	id: Mapped[int] = mapped_column(
		BigInteger,
		primary_key=True,
		autoincrement=True,
		comment="ID настроек пассивного дохода",
	)
	streamer_id: Mapped[int] = mapped_column(
		BigInteger,
		ForeignKey("users.telegram_id"),
		unique=True,
		nullable=False,
		comment="ID стримера, которому принадлежат настройки",
	)
	enabled: Mapped[bool] = mapped_column(
		Boolean,
		nullable=False,
		default=False,
		server_default="false",
		comment="Флаг включения пассивного дохода",
	)
	coins_per_interval: Mapped[int] = mapped_column(
		Integer,
		nullable=False,
		default=10,
		server_default="10",
		comment="Количество монет, начисляемых за интервал",
	)
	interval_minutes: Mapped[int] = mapped_column(
		Integer,
		nullable=False,
		default=5,
		server_default="5",
		comment="Интервал начисления монет в минутах",
	)
