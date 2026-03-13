from sqlalchemy import BigInteger, Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base


class AlertSettings(Base):
	__tablename__ = "alert_settings"

	id: Mapped[int] = mapped_column(
		BigInteger,
		primary_key=True,
		autoincrement=True,
		comment="ID правила доната в OBS виджете",
	)
	streamer_id: Mapped[int] = mapped_column(
		BigInteger,
		ForeignKey("users.telegram_id"),
		unique=True,
		nullable=False,
		comment="ID стримера, которому принадлежат правила доната",
	)
	bg_color: Mapped[str] = mapped_column(
		String(16),
		nullable=False,
		default="#1a1a2e",
		server_default="#1a1a2e",
		comment="Фоновый цвет доната",
	)
	text_color: Mapped[str] = mapped_column(
		String(16),
		nullable=False,
		default="#ffffff",
		server_default="#ffffff",
		comment="Цвет текста доната",
	)
	font: Mapped[str] = mapped_column(
		String(64),
		nullable=False,
		default="Roboto",
		server_default="Roboto",
		comment="Шрифт доната",
	)
	duration_sec: Mapped[int] = mapped_column(
		Integer,
		nullable=False,
		default=5,
		server_default="5",
		comment="Длительность доната",
	)
	image_enabled: Mapped[bool] = mapped_column(
		Boolean,
		nullable=False,
		default=True,
		server_default="true",
		comment="Флаг включения пикчи в донате",
	)
	tts_enabled: Mapped[bool] = mapped_column(
		Boolean,
		nullable=False,
		default=True,
		server_default="true",
		comment="Флаг включения озвучки доната",
	)
	tts_voice: Mapped[str] = mapped_column(
		String(64),
		nullable=False,
		default="silero_v3_ru",
		server_default="silero_v3_ru",
		comment="Голос озвучки доната",
	)
