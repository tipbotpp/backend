from sqlalchemy import BigInteger, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base
from src.models.mixins import TimestampMixin


class Users(Base, TimestampMixin):
	__tablename__ = "users"

	telegram_id: Mapped[int] = mapped_column(
		BigInteger,
		primary_key=True,
		nullable=False,
		comment="Telegram ID пользователя",
	)
	username: Mapped[str | None] = mapped_column(
		String(64),
		nullable=True,
		default=None,
		comment="Юзернейм пользователя в Telegram",
	)
	display_name: Mapped[str | None] = mapped_column(
		String(128),
		nullable=True,
		default=None,
		comment="Отображаемое имя пользователя",
	)
	description: Mapped[str | None] = mapped_column(
		Text,
		nullable=True,
		default=None,
		comment="Описание профиля пользователя",
	)
	avatar_url: Mapped[str | None] = mapped_column(
		String(512),
		nullable=True,
		default=None,
		comment="URL аватара пользователя",
	)
	role: Mapped[str | None] = mapped_column(
		String(16),
		nullable=True,
		default=None,
		comment="Роль пользователя: streamer | viewer | null",
	)
	balance: Mapped[int] = mapped_column(
		BigInteger,
		nullable=False,
		default=0,
		server_default="0",
		comment="Баланс пользователя в монетах",
	)
