class DonateText:
	@staticmethod
	def ask_streamer() -> str:
		return (
			"🎯 <b>Кому хочешь задонатить?</b>\n\n"
			"Введи username стримера (например: <code>@streamer</code>) или его Telegram ID:"
		)

	@staticmethod
	def streamer_not_found() -> str:
		return "❌ Стример не найден. Попробуй ещё раз или нажми Отмена."

	@staticmethod
	def streamer_no_active_stream(name: str) -> str:
		return f"❌ Стример <b>{name}</b> сейчас не в эфире."

	@staticmethod
	def ask_amount(streamer_name: str, balance: int) -> str:
		return (
			f"✅ Стример: <b>{streamer_name}</b>\n\n"
			f"💰 У тебя <b>{balance} монет</b>\n\n"
			"Введи сумму доната:"
		)

	@staticmethod
	def not_enough_balance(needed: int, balance: int) -> str:
		return (
			f"❌ Недостаточно монет.\n"
			f"Нужно: <b>{needed}</b> | На балансе: <b>{balance}</b>"
		)

	@staticmethod
	def invalid_amount() -> str:
		return "❌ Неверный формат. Введи целое число больше нуля."

	@staticmethod
	def ask_message() -> str:
		return "💬 Введи сообщение для стримера или нажми <b>Без сообщения</b>:"

	@staticmethod
	def success(streamer_name: str) -> str:
		return (
			f"🎉 <b>Донат отправлен!</b>\n\n"
			f"Стример <b>{streamer_name}</b> получит твой алерт!"
		)

	@staticmethod
	def notification_to_streamer(donor_name: str, amount: int, message: str | None) -> str:
		text = (
			f"💰 <b>Новый донат!</b>\n\n"
			f"От: <b>{donor_name}</b>\n"
			f"Сумма: <b>{amount} монет</b>"
		)
		if message:
			text += f"\nСообщение: «{message}»"
		return text

	@staticmethod
	def rejected_toxicity() -> str:
		return (
			"🚫 <b>Сообщение нарушает правила сообщества и было отклонено.</b>\n"
			"Монеты не списаны. Попробуй другой текст."
		)

	@staticmethod
	def rejected_stopword() -> str:
		return (
			"🚫 <b>Сообщение содержит запрещённое слово стримера.</b>\n"
			"Монеты не списаны."
		)

	@staticmethod
	def cancelled() -> str:
		return "❌ Отменено."
