from pydantic import BaseModel, Field


class App(BaseModel):
	title: str = Field(
		default="FastAPI Application",
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
	tz_offset_hours: float = Field(
		default=3.0,
		description=(
			"Смещение часового пояса относительно UTC.\n"
			"Когда менять → используйте 3.0 для Москвы."
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


class Logging(BaseModel):
	level: str = Field(
		default="INFO",
		description=(
			"Уровень логирования приложения.\n"
			"Когда менять → используйте `DEBUG` для разработки и отладки; "
			"`INFO` для продакшена; `WARNING` или выше для критических систем."
		),
	)
