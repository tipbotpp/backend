from pydantic import BaseModel, Field


class Database(BaseModel):
	"""
	Параметры подключения к PostgreSQL и настройки пула SQLAlchemy-asyncpg.
	В разделах «Когда менять» даны практические рекомендации.
	"""

	# ── Основные реквизиты подключения ──────────────────────────────────────────
	username: str = Field(
		default="postgres",
		description=(
			"Имя пользователя PostgreSQL.\n"
			"Когда менять → если в БД заведен иной логин или используется IAM/SSO-роль."
		),
	)
	db: str = Field(
		default="postgres",
		description=(
			"Название базы данных.\n"
			"Когда менять → указывайте имя продовой базы (например, `myapp_prod`)."
		),
	)
	port: int = Field(
		default=5432,
		description=(
			"Порт, на котором слушает PostgreSQL.\n"
			"Когда менять → если БД за NAT или порт нестандартный (Cloud SQL, RDS)."
		),
	)
	host: str = Field(
		default="localhost",
		description=(
			"Хост или IP сервера PostgreSQL.\n"
			"Когда менять → при выносе БД на отдельный узел/кластер."
		),
	)
	password: str = Field(
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
			"Когда менять → включайте на dev/CI для отладки; выключайте в проде."
		),
	)

	# ── Параметры пула соединений ───────────────────────────────────────────────
	pool_pre_ping: bool = Field(
		default=True,
		description=(
			"Пингует соединение (`SELECT 1`) перед выдачей из пула.\n"
			"Когда менять → `True`, если Docker/k8s/LB может закрывать idle-соединения."
		),
	)
	pool_recycle: int = Field(
		default=1800,
		description=(
			"Максимальный «возраст» соединения (сек).\n"
			"Типично: 900–3600 с (15–60 мин)."
		),
	)
	pool_use_lifo: bool = Field(
		default=True,
		description=(
			"Использовать LIFO вместо FIFO.\n"
			"Типично: `True` для больших пулов (>20) или всплесковой нагрузки."
		),
	)
	pool_timeout: int = Field(
		default=30,
		description=(
			"Сколько секунд ждать свободный коннект, когда пул исчерпан.\n"
			"Типично: 10–60 с."
		),
	)
	pool_size: int = Field(
		default=5,
		description=(
			"Базовое количество постоянных соединений.\n"
			"Типично: 2–8 × число async-воркеров, но не больше лимита БД."
		),
	)
	max_overflow: int = Field(
		default=10,
		description=(
			"Максимум «временных» соединений сверх `pool_size`.\n"
			"Типично: 1–4 × pool_size."
		),
	)

	@property
	def async_database_url(self) -> str:
		return "postgresql+asyncpg://%s:%s@%s:%d/%s" % (
			self.username,
			self.password,
			self.host,
			self.port,
			self.db,
		)
