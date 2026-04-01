from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base
from src.utils import local_time


class Donations(Base):
	__tablename__ = "donations"

	id: Mapped[int] = mapped_column(
		BigInteger,
		primary_key=True,
		autoincrement=True,
		comment="ID доната",
	)
	from_user_id: Mapped[int] = mapped_column(
		BigInteger,
		ForeignKey("users.telegram_id"),
		nullable=False,
		comment="ID пользователя, отправившего донат",
	)
	to_streamer_id: Mapped[int] = mapped_column(
		BigInteger,
		ForeignKey("users.telegram_id"),
		nullable=False,
		comment="ID стримера, получившего донат",
	)
	session_id: Mapped[int] = mapped_column(
		BigInteger,
		ForeignKey("stream_sessions.id"),
		nullable=False,
		comment="ID стрим-сессии, в которой был отправлен донат",
	)
	amount: Mapped[int] = mapped_column(
		BigInteger,
		nullable=False,
		comment="Сумма доната в монетах",
	)
	message: Mapped[str | None] = mapped_column(
		Text,
		nullable=True,
		default=None,
		comment="Сообщение к донату",
	)
	status: Mapped[str] = mapped_column(
		String(16),
		nullable=False,
		comment="Статус доната: processing | delivered | rejected",
	)
	reject_reason: Mapped[str | None] = mapped_column(
		String(16),
		nullable=True,
		default=None,
		comment="Причина отклонения доната: toxicity | stopword | nsfw | null",
	)
	audio_url: Mapped[str | None] = mapped_column(
		String(512),
		nullable=True,
		default=None,
		comment="URL аудио TTS-озвучки доната",
	)
	image_url: Mapped[str | None] = mapped_column(
		String(512),
		nullable=True,
		default=None,
		comment="URL картинки к донату",
	)
	created_at: Mapped[datetime] = mapped_column(
		DateTime(timezone=True),
		nullable=False,
		default=local_time.now,
		server_default=func.now(),
		comment="Дата и время создания доната",
	)
