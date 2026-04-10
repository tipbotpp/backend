class StartText:
	@staticmethod
	def welcome_new(name: str) -> str:
		return (
			f"👋 Привет, <b>{name}</b>!\n\n"
			"Добро пожаловать в <b>TipBot</b> — платформу донатов для стримеров.\n\n"
			"Кем ты являешься?"
		)

	@staticmethod
	def welcome_viewer(name: str) -> str:
		return (
			f"👋 Привет, <b>{name}</b>!\n\n"
			"Ты зритель. Открывай Mini App, отправляй донаты и получай монеты за просмотр стримов."
		)

	@staticmethod
	def welcome_streamer(name: str) -> str:
		return (
			f"👋 Привет, <b>{name}</b>!\n\n"
			"Ты стример. Управляй стримом прямо из бота."
		)

	@staticmethod
	def role_set_viewer() -> str:
		return (
			"✅ Роль <b>зрителя</b> выбрана!\n\n"
			"На твой счёт начислено <b>100 монет</b> 🪙\n\n"
			"Открывай Mini App и начинай донатить любимым стримерам."
		)

	@staticmethod
	def role_set_streamer() -> str:
		return (
			"✅ Роль <b>стримера</b> выбрана!\n\n"
			"Теперь ты можешь запускать стримы и получать донаты."
		)

	@staticmethod
	def role_already_set() -> str:
		return "⚠️ Роль уже выбрана и не может быть изменена."
