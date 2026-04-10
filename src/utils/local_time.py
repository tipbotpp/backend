from datetime import date, datetime

from src.core.configs import cfg


def now() -> datetime:
	return datetime.now(cfg.tz)


def today() -> date:
	return now().date()


def remove_timezone(dt: datetime | None) -> datetime | None:
	if dt and hasattr(dt, "tzinfo") and dt.tzinfo is not None:
		return dt.astimezone(cfg.tz).replace(tzinfo=None)
	return dt
