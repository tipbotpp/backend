from __future__ import annotations

from datetime import datetime


class StreamText:
	@staticmethod
	def inactive() -> str:
		return "🔴 Стрим не активен.\n\nНажми кнопку, чтобы начать стрим и получить ссылку для OBS."

	@staticmethod
	def started(widget_url: str) -> str:
		return (
			"🟢 <b>Стрим запущен!</b>\n\n"
			"🔗 Ссылка для OBS (нажми, чтобы скопировать):\n"
			f"<code>{widget_url}</code>\n\n"
			"Добавь эту ссылку как <b>Browser Source</b> в OBS."
		)

	@staticmethod
	def already_active(widget_url: str, started_at: datetime) -> str:
		return (
			"🟢 <b>Стрим уже идёт</b>\n\n"
			f"🕐 Начат: {started_at.strftime('%H:%M')}\n\n"
			"🔗 Ссылка для OBS:\n"
			f"<code>{widget_url}</code>"
		)

	@staticmethod
	def stopped(
		total_collected: int,
		donations_count: int,
		duration_seconds: int,
	) -> str:
		hours, remainder = divmod(duration_seconds, 3600)
		minutes = remainder // 60
		duration_str = f"{hours}ч {minutes}м" if hours else f"{minutes}м"
		return (
			"⏹ <b>Стрим завершён!</b>\n\n"
			"📊 <b>Итоги сессии:</b>\n"
			f"💰 Собрано: {total_collected} монет\n"
			f"🎁 Донатов: {donations_count}\n"
			f"⏱ Длительность: {duration_str}"
		)

	@staticmethod
	def not_active() -> str:
		return "❌ Нет активного стрима."

	@staticmethod
	def streamer_only() -> str:
		return "❌ Управление стримом доступно только для стримеров."

	@staticmethod
	def help_text() -> str:
		return (
			"ℹ️ <b>TipBot</b> — платформа донатов для стримеров.\n\n"
			"<b>Зрители:</b> отправляй монеты стримерам и получай пассивный доход во время стримов.\n"
			"<b>Стримеры:</b> принимай донаты с голосовыми алертами прямо в OBS.\n\n"
			"<b>Команды:</b>\n"
			"/start — главное меню\n"
			"/balance — текущий баланс (для зрителей)\n"
			"/stream — управление стримом (для стримеров)\n"
			"/help — эта справка"
		)
