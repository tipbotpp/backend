from sqlalchemy import BigInteger, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base


class StopWords(Base):
	__tablename__ = "stop_words"

	STREAMER_WORD_CONSTRAINT = UniqueConstraint(
		"streamer_id",
		"word",
		name="uq_stop_words_streamer_word",
	)

	id: Mapped[int] = mapped_column(
		BigInteger,
		primary_key=True,
		autoincrement=True,
		comment="ID стоп-слова",
	)
	streamer_id: Mapped[int] = mapped_column(
		BigInteger,
		ForeignKey("users.telegram_id"),
		nullable=False,
		comment="ID стримера, которому принадлежит стоп-слово",
	)
	word: Mapped[str] = mapped_column(
		String(128),
		nullable=False,
		comment="Стоп-слово для фильтрации донатов",
	)
