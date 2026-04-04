class BalanceText:
	@staticmethod
	def balance_info(balance: int) -> str:
		return f"💰 Твой баланс: <b>{balance} монет</b>"

	@staticmethod
	def topup_menu(balance: int) -> str:
		return (
			f"💳 <b>Пополнение баланса</b>\n\n"
			f"Текущий баланс: <b>{balance} монет</b>\n\n"
			"Выбери сумму или введи свою:"
		)

	@staticmethod
	def topup_ask_amount() -> str:
		return "✏️ Введи сумму пополнения (например: 250):"

	@staticmethod
	def topup_success(added: int, new_balance: int) -> str:
		return (
			f"✅ Баланс пополнен!\n\n"
			f"Начислено: <b>+{added} монет</b>\n"
			f"Текущий баланс: <b>{new_balance} монет</b>"
		)

	@staticmethod
	def topup_invalid_amount() -> str:
		return "❌ Неверный формат. Введи целое число больше нуля."

	@staticmethod
	def cancelled() -> str:
		return "❌ Отменено."
