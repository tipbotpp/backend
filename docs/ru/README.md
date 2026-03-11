# fastapi-template

Production-ready шаблон для REST API на FastAPI.

## Быстрый старт

```bash
git clone https://github.com/your-repo/fastapi_template.git my-api
cd my-api
uv sync --dev
cp config.example.toml config.toml
# отредактируй config.toml
make run
```

## Конфигурация

Приложение поддерживает три источника конфигурации (по приоритету):

1. **Переменные окружения** (высший приоритет, разделитель вложенности `__`)
2. **config.json**
3. **config.toml**

Пример: `APP__PORT=3000` переопределит `app.port` из TOML.

### Секции конфигурации

| Секция | Описание |
|--------|----------|
| `[app]` | Название, хост, порт, workers, CORS, пагинация |
| `[database]` | PostgreSQL: хост, порт, логин, пароль + настройки пула соединений |
| `[redis]` | Redis: хост, порт, пароль, размер пула |
| `[s3]` | S3/MinIO: хосты (internal/external), ключи, бакет |
| `[logging]` | Уровень логирования (DEBUG/INFO/WARNING/ERROR) |

## Архитектура

```
src/
├── api/           — слой API (роуты, зависимости)
├── core/          — инфраструктура (БД, кеш, S3, конфиг)
├── di/            — DI-контейнер (dishka)
├── models/        — SQLAlchemy-модели
├── repos/         — репозитории (sql/redis/s3)
├── services/      — бизнес-логика
├── schemas/       — DTO, enum'ы, Pydantic-схемы
└── utils/         — утилиты
```

### Слой API (`src/api/`)

Каждая фича оформляется как набор файлов:

- **`routes/`** — роутеры с эндпоинтами
- **`dependencies/`** — FastAPI зависимости
- **`schemas/`** — Pydantic-схемы запросов/ответов

```python
# api/routes/users.py
from dishka import FromDishka
from fastapi import APIRouter

from src.services import UserService

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/{user_id}")
async def get_user(
    user_id: int,
    service: FromDishka[UserService],
):
    return await service.get_by_id(user_id)
```

### Dependency Injection (dishka)

Три провайдера с разными скоупами:

| Провайдер | Scope | Что предоставляет |
|-----------|-------|-------------------|
| `CoreProvider` | APP | AsyncEngine, session_factory, Redis pool, Redis client, Logger |
| `RequestProvider` | REQUEST | S3 клиенты (internal/external) |
| `RepositoryProvider` | REQUEST | AsyncSession, репозитории |
| `ServiceProvider` | REQUEST | Сервисы бизнес-логики |

APP-скоуп — синглтоны на всё время жизни приложения. REQUEST-скоуп — новый экземпляр на каждый HTTP-запрос.

### Репозитории

Абстрактные интерфейсы для инфраструктурного слоя (подмена реализации в тестах):

- **`AbstractBaseRepository[ModelT]`** — CRUD для SQL (get_by_id, get_all, create, update, delete)
- **`AbstractCacheRepository`** — кеш (get, set, delete, exists, get_many, set_many)
- **`AbstractS3Repository`** — файлы (upload, download, delete, exists, presigned_url)

### Модели и миксины

- **`TimestampMixin`** — автоматические `created_at` / `updated_at`
- **`SoftDeleteMixin`** — мягкое удаление (`deleted_at`), автофильтрация SELECT-запросов

```python
class User(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(unique=True)
```

### Middleware

- **`HTTPLoggingMiddleware`** — логирование HTTP-запросов (path, method, status, время)
- **`CORSMiddleware`** — CORS-заголовки
- **`GZipMiddleware`** — сжатие ответов

### Обработка ошибок

Централизованные exception handlers для:
- `ValueError`, `HTTPStatusError`, `RequestError`
- `IntegrityError`, `UniqueViolationError`
- `PyJWTError`
- Generic `Exception`

## Docker

```bash
docker build -t my-api .
docker run --env-file .env -p 8000:8000 my-api
```

Dockerfile: multi-stage build, non-root user, автоматические миграции при старте.

## CI/CD (GitHub Actions)

| Workflow | Триггер | Что делает |
|----------|---------|------------|
| `tests.yml` | push/PR | pytest |
| `lint.yml` | push/PR | ruff |
| `typecheck.yml` | push/PR | ty |
| `dev.yml` | push в dev | Деплой на dev-сервер |
| `main.yml` | push в main | Деплой на прод |

## Make-команды

```bash
make run              # Запуск сервера
make format           # Форматирование (ruff)
make lint             # Проверка кода (ruff)
make revision         # Создать миграцию alembic
make upgrade          # Применить миграции
make test             # Unit-тесты
make test/coverage    # Тесты с покрытием
```
