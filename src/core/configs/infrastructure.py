from pydantic import BaseModel, Field


class MLService(BaseModel):
	host: str = Field(
		default="http://ml-service:8001",
		description=(
			"Базовый URL ML-сервиса.\n"
			"Когда менять → при смене адреса ML-сервиса в docker-сети."
		),
	)
	internal_secret: str = Field(
		default="",
		description=(
			"Shared secret для заголовка X-Internal-Secret.\n"
			"Когда менять → всегда указывайте в проде; лучше хранить в секрет-менеджере."
		),
	)
	timeout_seconds: int = Field(
		default=30,
		description=(
			"Таймаут запросов к ML-сервису в секундах.\n"
			"Когда менять → увеличивайте при медленных моделях."
		),
	)


class S3(BaseModel):
	aws_host: str = Field(
		default="http://localhost:9000",
		description=(
			"Адрес S3-хранилища.\n"
			"Когда менять → указывайте адрес вашего S3-хранилища "
			"(например, `https://s3.amazonaws.com` для AWS S3)."
		),
	)
	aws_host_internal: str | None = Field(
		default=None,
		description=(
			"Адрес внутреннего S3-хранилища (если отличается от внешнего).\n"
			"Когда менять → указывайте, если используете разные адреса "
			"для внутренних и внешних запросов (например, в k8s-кластере)."
		),
	)
	aws_host_external: str | None = Field(
		default=None,
		description=(
			"Адрес внешнего S3-хранилища (если отличается от внутреннего).\n"
			"Когда менять → указывайте, если используете разные адреса "
			"для внутренних и внешних запросов (например, в k8s-кластере)."
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
			"Когда менять → указывайте, если ваше S3-хранилище требует региона."
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
	presigned_url_ttl: int = Field(
		default=3600,
		description=(
			"TTL presigned URL в секундах.\n"
			"Когда менять → уменьшайте для повышения безопасности, "
			"увеличивайте если клиенты кешируют ссылки надолго."
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

	host: str = Field(
		default="localhost",
		description=(
			"Хост Redis сервера.\n"
			"Когда менять → при выносе Redis на отдельный узел/кластер."
		),
	)
	port: int = Field(
		default=6379,
		description=(
			"Порт Redis сервера.\n"
			"Когда менять → если Redis использует нестандартный порт."
		),
	)
	db: int = Field(
		default=0,
		description=(
			"Номер базы данных Redis (0-15).\n"
			"Когда менять → используйте разные БД для разных целей."
		),
	)
	password: str | None = Field(
		default=None,
		description=(
			"Пароль для подключения к Redis.\n"
			"Когда менять → всегда устанавливайте в проде; лучше хранить в секрет-менеджере."
		),
	)
	max_connections: int = Field(
		default=10,
		description=(
			"Максимальное количество соединений в пуле.\n"
			"Когда менять → увеличивайте при высокой нагрузке."
		),
	)
	socket_timeout: int = Field(
		default=5,
		description=(
			"Таймаут сокета в секундах.\n"
			"Когда менять → увеличивайте при медленной сети."
		),
	)
	socket_connect_timeout: int = Field(
		default=5,
		description=(
			"Таймаут подключения в секундах.\n"
			"Когда менять → увеличивайте при медленной сети."
		),
	)
