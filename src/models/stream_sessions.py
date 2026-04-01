from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base
from src.utils import local_time


class StreamSessions(Base):
	__tablename__ = "stream_sessions"

	id: Mapped[int] = mapped_column(
		BigInteger,
		primary_key=True,
		autoincrement=True,
		comment="ID стрим-сессии",
	)
	streamer_id: Mapped[int] = mapped_column(
		BigInteger,
		ForeignKey("users.telegram_id"),
		nullable=False,
		comment="ID стримера, которому принадлежит сессия",
	)
	stream_token: Mapped[str] = mapped_column(
		String(64),
		unique=True,
		nullable=False,
		comment="Уникальный токен стрим-сессии для OBS-виджета",
	)
	is_active: Mapped[bool] = mapped_column(
		Boolean,
		nullable=False,
		default=True,
		server_default="true",
		comment="Флаг активности стрим-сессии",
	)
	passive_income_enabled: Mapped[bool] = mapped_column(
		Boolean,
		nullable=False,
		default=False,
		server_default="false",
		comment="Флаг включения пассивного дохода для зрителей во время стрима",
	)
	started_at: Mapped[datetime] = mapped_column(
		DateTime(timezone=True),
		nullable=False,
		default=local_time.now,
		server_default=func.now(),
		comment="Дата и время начала стрима",
	)
	ended_at: Mapped[datetime | None] = mapped_column(
		DateTime(timezone=True),
		nullable=True,
		default=None,
		comment="Дата и время окончания стрима",
	)
