from datetime import date, datetime

from src.core.config import cfg


class DateTimeLocal:
	@staticmethod
	def now() -> datetime:
		return datetime.now(cfg.tz)

	@staticmethod
	def today() -> date:
		return DateTimeLocal.now().date()

	@staticmethod
	def remove_timezone(dt: datetime | None) -> datetime | None:
		if dt and hasattr(dt, "tzinfo") and dt.tzinfo is not None:
			return dt.astimezone(cfg.tz).replace(tzinfo=None)
		return dt
