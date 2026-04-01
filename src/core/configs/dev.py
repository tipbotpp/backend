from pydantic import BaseModel, Field


class Dev(BaseModel):
	enabled: bool = Field(
		default=False,
		description=(
			"Включает dev-режим: обход валидации initData для тестового пользователя.\n"
			"Когда менять → только в dev-окружении, НИКОГДА в проде."
		),
	)
	telegram_id: int = Field(
		default=100000001,
		description="Telegram ID тестового dev-пользователя.",
	)
	username: str = Field(
		default="dev_user",
		description="Username тестового dev-пользователя.",
	)
	display_name: str = Field(
		default="Dev User",
		description="Отображаемое имя тестового dev-пользователя.",
	)
	mock_init_data: str = Field(
		default="",
		description=(
			"Секретный токен, который заменяет настоящий initData в dev-режиме.\n"
			"Передаётся в заголовке Authorization: Bearer <mock_init_data> вместо JWT."
		),
	)
