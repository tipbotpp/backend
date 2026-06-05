from pydantic import BaseModel, Field


class App(BaseModel):
	title: str = Field(
		default="TipBot API",
		description=(
			"Название приложения, отображаемое в документации и заголовке сервера.\n"
			"Когда менять → используйте понятное название вашего приложения."
		),
	)
	host: str = Field(
		default="0.0.0.0",
		description=(
			"Адрес, на котором будет запущен FastAPI-сервер.\n"
			"Когда менять → используйте `0.0.0.0` для доступа извне; "
			"`localhost` для локальной разработки или CI."
		),
	)
	port: int = Field(
		default=8000,
		description=(
			"Порт, на котором будет запущен FastAPI-сервер.\n"
			"Когда менять → используйте 8000 для dev/CI; "
			"в проде выбирайте порт, который не конфликтует с другими сервисами."
		),
	)
	workers: int = Field(
		default=1,
		description=(
			"Количество воркеров для обработки запросов.\n"
			"Когда менять → увеличивайте при высокой нагрузке, "
			"но не более 2–4 × количество ядер CPU."
		),
	)
	reload: bool = Field(
		default=False,
		description=(
			"Включает режим перезагрузки сервера при изменении кода.\n"
			"Когда менять → включайте на dev/CI для разработки; выключайте в проде."
		),
	)
	debug: bool = Field(
		default=False,
		description=(
			"Включает режим отладки FastAPI.\n"
			"Когда менять → включайте на dev/CI для отладки; выключайте в проде."
		),
	)
	tz_name: str = Field(
		default="Europe/Moscow",
		description=(
			"IANA-имя часового пояса (например, 'Europe/Moscow', 'UTC', 'America/New_York').\n"
			"Когда менять → укажите нужный часовой пояс для вашего окружения."
		),
	)
	default_offset: int = Field(
		default=0,
		description="Смещение по умолчанию для пагинации.",
	)
	default_limit: int = Field(
		default=20,
		description=(
			"Количество элементов по умолчанию в одном запросе.\n"
			"Когда менять → увеличивайте при необходимости, но не более 100."
		),
	)
	maximum_limit: int = Field(
		default=100,
		description=(
			"Максимальное количество элементов в одном запросе.\n"
			"Когда менять → увеличивайте при необходимости, но не более 500."
		),
	)
	allow_origins: list[str] = Field(
		default_factory=lambda: ["*"],
		description=(
			"Список разрешённых CORS-источников.\n"
			"Когда менять → указывайте конкретные домены в проде."
		),
	)
	mini_app_url: str = Field(
		default="https://t.me/your_bot/app",
		description=(
			"URL Telegram Mini App.\n"
			"Когда менять → укажите ссылку вида https://t.me/<bot>/<app_short_name>."
		),
	)
	public_url: str = Field(
		default="https://tipbot.example.com",
		description=(
			"Публичный базовый URL бэкенда (без слеша на конце).\n"
			"Используется для формирования ws_url.\n"
			"Когда менять → укажите реальный домен в проде."
		),
	)
	widget_base_url: str = Field(
		default="https://tipbot.example.com",
		description=(
			"Публичный базовый URL фронтенда (без слеша на конце).\n"
			"Используется для формирования widget_url — ссылки на OBS Browser Source.\n"
			"Когда менять → укажите домен фронтенда в проде."
		),
	)


class Auth(BaseModel):
	jwt_private_key: str = Field(
		default="",
		description=(
			"RSA приватный ключ в формате PEM для подписи JWT (RS256).\n"
			"Генерация: `openssl genrsa -out private.pem 2048`\n"
			"Когда менять → генерируйте уникальную пару ключей для каждого окружения."
		),
	)
	jwt_public_key: str = Field(
		default="",
		description=(
			"RSA публичный ключ в формате PEM для верификации JWT.\n"
			"Генерация: `openssl rsa -in private.pem -pubout -out public.pem`\n"
			"Можно раздавать другим сервисам — они верифицируют токены без приватного ключа."
		),
	)
	jwt_algorithm: str = Field(
		default="RS256",
		description="Алгоритм подписи JWT. RS256 — асимметричный, рекомендуется для мультисервисной архитектуры.",
	)
	jwt_expire_seconds: int = Field(
		default=2592000,
		description="Время жизни JWT токена в секундах. По умолчанию 30 дней.",
	)


class Logging(BaseModel):
	level: str = Field(
		default="INFO",
		description=(
			"Уровень логирования приложения.\n"
			"Когда менять → используйте `DEBUG` для разработки и отладки; "
			"`INFO` для продакшена; `WARNING` или выше для критических систем."
		),
	)
