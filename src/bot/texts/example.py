class StartText:
	@classmethod
	def greeting(cls, name: str) -> str:
		return f"""Привет, {name}! 👋
Я — бот-шаблон на aiogram.

Нажми /help, чтобы узнать, что я умею."""

	@classmethod
	def help(cls) -> str:
		return """📋 <b>Доступные команды:</b>

/start — начать работу
/help — список команд"""
