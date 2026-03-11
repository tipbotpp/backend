from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base
from src.models.mixins import SoftDeleteMixin, TimestampMixin


class User(Base, TimestampMixin, SoftDeleteMixin):
	__tablename__ = "users"

	id: Mapped[int] = mapped_column(primary_key=True)
	email: Mapped[str] = mapped_column(String(255), unique=True)
	password_hash: Mapped[str | None] = mapped_column(String(255), default=None)
	first_name: Mapped[str | None] = mapped_column(String(255), default=None)
	last_name: Mapped[str | None] = mapped_column(String(255), default=None)
