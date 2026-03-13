from pydantic import BaseModel, Field


class Bot(BaseModel):
	"""
	Параметры Telegram-бота.
	"""

	token: str = Field(
		default="",
		description=(
			"Токен Telegram-бота, полученный от @BotFather.\n"
			"Когда менять → всегда указывайте; в проде хранить в секрет-менеджере."
		),
	)
	debug: bool = Field(
		default=False,
		description=(
			"Включает режим отладки бота.\n"
			"Когда менять → включайте на dev/CI для отладки; выключайте в проде."
		),
	)
	drop_pending_updates: bool = Field(
		default=True,
		description=(
			"Пропускать накопившиеся update'ы при старте бота.\n"
			"Когда менять → `True` для прода, чтобы не обрабатывать старые сообщения; "
			"`False` для отладки."
		),
	)
