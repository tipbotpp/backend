from datetime import timedelta, timezone
from pathlib import Path

from pydantic import BaseModel, Field
from pydantic_settings import (
	BaseSettings,
	EnvSettingsSource,
	JsonConfigSettingsSource,
	PydanticBaseSettingsSource,
	SettingsConfigDict,
	TomlConfigSettingsSource,
)

if __name__ == "__main__":
	import sys

	BASE_DIR = Path(__file__).parent.parent.parent.parent
	sys.path.append(str(BASE_DIR))

BASE_DIR = Path(__file__).parent.parent.parent.parent
ENV_PATH = BASE_DIR.joinpath(".env")
JSON_SETTINGS_PATH = BASE_DIR.joinpath("config.json")
TOML_SETTINGS_PATH = BASE_DIR.joinpath("config.toml")

PathsSourcesDict: dict[Path, type[PydanticBaseSettingsSource]] = {
	TOML_SETTINGS_PATH: TomlConfigSettingsSource,
	JSON_SETTINGS_PATH: JsonConfigSettingsSource,
	ENV_PATH: EnvSettingsSource,
}


class ExampleConfig(BaseModel):
	"""
	Пример блока конфигурации
	"""

	example_field: str = Field(
		default="examle",
		description=(
			"Пример поля для блока конфигурации"
		),
	)

	@property
	def example_property(self) -> str:
		"""

		:return:
		"""
		return "example"

class Database(BaseModel):
	"""
	Параметры подключения к PostgreSQL и настройки пула SQLAlchemy-asyncpg.
	В разделах «Когда менять» даны практические рекомендации.
	"""

	# ── Основные реквизиты подключения ──────────────────────────────────────────
	postgres_username: str = Field(
		default="postgres",
		description=(
			"Имя пользователя PostgreSQL.\n"
			"Когда менять → если в БД заведен иной логин или используется IAM/SSO-роль."
		),
	)
	postgres_db: str = Field(
		default="postgres",
		description=(
			"Название базы/схемы.\n"
			"Когда менять → указывайте имя продовой базы (например, `myapp_prod`)."
		),
	)
	postgres_port: int = Field(
		default=5432,
		description=(
			"Порт, на котором слушает PostgreSQL.\n"
			"Когда менять → если БД за NAT или порт нестандартный (Cloud SQL, RDS)."
		),
	)
	postgres_host: str = Field(
		default="localhost",
		description=(
			"Хост или IP сервера PostgreSQL.\n"
			"Когда менять → при выносе БД на отдельный узел/кластер."
		),
	)
	postgres_password: str = Field(
		default="postgres",
		description=(
			"Пароль указанного пользователя.\n"
			"Когда менять → всегда в проде; лучше хранить в секрет-менеджере."
		),
	)

	# ── Логирование ─────────────────────────────────────────────────────────────
	echo: bool = Field(
		default=True,
		description=(
			"Включить подробный SQL-лог (`echo=True`).\n"
			"Когда менять → включайте на dev/CI для отладки; выключайте в проде, "
			"чтобы не заливать логи SQL-трафиком."
		),
	)

	# ── Параметры пула соединений ───────────────────────────────────────────────
	pool_pre_ping: bool = Field(
		default=True,
		description=(
			"Пингует соединение (`SELECT 1`) перед выдачей из пула, выбрасывая "
			"«мертвые» коннекты.\n"
			"🔸 Типично: `True`.\n"
			"Когда менять → ставьте `True`, если Docker/k8s/LB может закрывать "
			"idle-соединения; можно `False` лишь при гарантии стабильной сети и "
			"желании убрать лишний запрос."
		),
	)
	pool_recycle: int = Field(
		default=1800,
		description=(
			"Максимальный «возраст» соединения (сек). Старая сессия закрывается и "
			"открывается заново, предотвращая idle-тайм-ауты.\n"
			"🔸 Типично: 900–3600 с (15–60 мин).\n"
			"Когда менять → если сеть/Proxy убивает idle быстрее: ставьте чуть меньше "
			"observed idle-timeout; `-1` полностью отключает механизм."
		),
	)
	pool_use_lifo: bool = Field(
		default=True,
		description=(
			"Использовать LIFO вместо FIFO: последний освободившийся коннект "
			"выдаётся первым, снижая шанс «застоя».\n"
			"🔸 Типично: `True` для больших пулов (>20) или всплесковой нагрузки.\n"
			"Когда менять → если pool_size маленький (≤10) и нагрузка ровная, "
			"`False` достаточно."
		),
	)
	pool_timeout: int = Field(
		default=30,
		description=(
			"Сколько секунд ждать свободный коннект, когда пул исчерпан "
			"(`pool_size + max_overflow`). Затем бросается `TimeoutError`.\n"
			"🔸 Типично: 10–60 с.\n"
			"Когда менять → увеличьте, если короткие пики нагрузки вызывают тайм-ауты; "
			"уменьшите, если важна быстрая ошибка и ретрай."
		),
	)
	pool_size: int = Field(
		default=5,
		description=(
			"Базовое количество постоянных соединений.\n"
			"🔸 Типично: 2–8 × число async-воркеров, но не больше лимита БД.\n"
			"Когда менять → повышайте при I/O-тяжёлых запросах и свободных "
			"ресурсах БД; уменьшайте, если БД перегружена."
		),
	)
	max_overflow: int = Field(
		default=10,
		description=(
			"Максимум «временных» соединений сверх `pool_size`, создаваемых при "
			"спайках нагрузки. Эти коннекты закрываются при возврате.\n"
			"🔸 Типично: 1–4 × pool_size.\n"
			"Когда менять → увеличьте, если видите `TimeoutError`, а CPU БД свободен; "
			"уменьшите, если БД захлёбывается в пиках."
		),
	)

	@property
	def async_database_url(self) -> str:
		return "postgresql+asyncpg://%s:%s@%s:%d/%s" % (
			self.postgres_username,
			self.postgres_password,
			self.postgres_host,
			self.postgres_port,
			self.postgres_db,
		)


class App(BaseModel):
	"""
	Параметры FastAPI приложения.
	"""

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
			"Когда менять → включайте на dev/CI для разработки; "
			"выключайте в проде."
		),
	)
	debug: bool = Field(
		default=False,
		description=(
			"Включает режим отладки FastAPI.\n"
			"Когда менять → включайте на dev/CI для отладки; "
			"выключайте в проде, чтобы не раскрывать детали реализации."
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
		description=(
			"Смещение по умолчанию для пагинации.\n"
			"Когда менять → обычно оставляйте 0."
		),
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


class S3(BaseModel):
	aws_host: str = Field(
		default="http://localhost:9000",
		description=(
			"Адрес S3-хранилища.\n"
			"Когда менять → указывайте адрес вашего S3-хранилища (например, "
			"`https://s3.amazonaws.com` для AWS S3)."
		),
	)
	aws_host_internal: str | None = Field(
		default=None,
		description=(
			"Адрес внутреннего S3-хранилища (если отличается от внешнего).\n"
			"Когда менять → указывайте, если используете разные адреса для "
			"внутренних и внешних запросов (например, в k8s-кластере)."
		),
	)
	aws_host_external: str | None = Field(
		default=None,
		description=(
			"Адрес внешнего S3-хранилища (если отличается от внутреннего).\n"
			"Когда менять → указывайте, если используете разные адреса для "
			"внутренних и внешних запросов (например, в k8s-кластере)."
		),
	)
	aws_access_key: str = Field(
		default="",
		description=(
			"Ключ доступа к S3-хранилищу.\n"
			"Когда менять → указывайте ваш ключ доступа; "
			"в проде лучше хранить в секрет-менеджере."
		),
	)
	aws_secret_access_key: str = Field(
		default="",
		description=(
			"Секретный ключ доступа к S3-хранилищу.\n"
			"Когда менять → указывайте ваш секретный ключ; "
			"в проде лучше хранить в секрет-менеджере."
		),
	)
	aws_region: str | None = Field(
		default=None,
		description=(
			"Регион S3-хранилища (если требуется).\n"
			"Когда менять → указывайте, если ваше S3-хранилище требует указания региона; "
			"в противном случае можно оставить пустым."
		),
	)
	aws_bucket: str = Field(
		default="",
		description=(
			"Имя S3-бакета, в котором будут храниться файлы.\n"
			"Когда менять → указывайте имя вашего бакета; "
			"в проде лучше хранить в секрет-менеджере."
		),
	)

	@property
	def internal_host(self) -> str:
		return self.aws_host_internal or self.aws_host

	@property
	def external_host(self) -> str:
		return self.aws_host_external or self.aws_host


class Redis(BaseModel):
	"""
	Параметры подключения к Redis.
	"""

	redis_host: str = Field(
		default="localhost",
		description=(
			"Хост Redis сервера.\n"
			"Когда менять → при выносе Redis на отдельный узел/кластер."
		),
	)
	redis_port: int = Field(
		default=6379,
		description=(
			"Порт Redis сервера.\n"
			"Когда менять → если Redis использует нестандартный порт."
		),
	)
	redis_db: int = Field(
		default=0,
		description=(
			"Номер базы данных Redis (0-15).\n"
			"Когда менять → используйте разные БД для разных целей (кеш, сессии и т.д.)."
		),
	)
	redis_password: str | None = Field(
		default=None,
		description=(
			"Пароль для подключения к Redis.\n"
			"Когда менять → всегда устанавливайте в проде; лучше хранить в секрет-менеджере."
		),
	)
	redis_max_connections: int = Field(
		default=10,
		description=(
			"Максимальное количество соединений в пуле.\n"
			"Когда менять → увеличивайте при высокой нагрузке."
		),
	)
	redis_socket_timeout: int = Field(
		default=5,
		description=(
			"Таймаут сокета в секундах.\n"
			"Когда менять → увеличивайте при медленной сети."
		),
	)
	redis_socket_connect_timeout: int = Field(
		default=5,
		description=(
			"Таймаут подключения в секундах.\n"
			"Когда менять → увеличивайте при медленной сети."
		),
	)


class Config(BaseSettings):
	model_config = SettingsConfigDict(
		extra="ignore",
		env_file=ENV_PATH,
		json_file=JSON_SETTINGS_PATH,
		toml_file=TOML_SETTINGS_PATH,
		env_file_encoding="utf-8",
		env_nested_delimiter="__",
		case_sensitive=False,
	)

	example: ExampleConfig = ExampleConfig()
	database: Database = Database()
	app: App = App()
	s3: S3 = S3()
	logging: Logging = Logging()
	redis: Redis = Redis()

	@property
	def tz(self) -> timezone:
		return timezone(
			offset=timedelta(hours=self.app.tz_offset_hours),
			name="Europe/Moscow",
		)

	@classmethod
	def settings_customise_sources(
		cls,
		settings_cls: type[BaseSettings],
		init_settings: PydanticBaseSettingsSource,  # noqa: ARG003
		env_settings: PydanticBaseSettingsSource,  # noqa: ARG003
		dotenv_settings: PydanticBaseSettingsSource,  # noqa: ARG003
		file_secret_settings: PydanticBaseSettingsSource,  # noqa: ARG003
	) -> tuple[PydanticBaseSettingsSource, ...]:
		res = [
			method(settings_cls)
			for path, method in PathsSourcesDict.items()
			if path.exists()
		]
		return EnvSettingsSource(settings_cls), *res


settings = Config()

if __name__ == "__main__":
	print(BASE_DIR)
	print(settings.model_dump_json(indent=2))
