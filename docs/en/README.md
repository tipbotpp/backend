# fastapi-template

Production-ready template for REST APIs built with FastAPI.

## Quick start

```bash
git clone https://github.com/your-repo/fastapi_template.git my-api
cd my-api
uv sync --dev
cp config.example.toml config.toml
# edit config.toml
make run
```

## Configuration

The app supports three config sources (by priority):

1. **Environment variables** (highest priority, nesting delimiter `__`)
2. **config.json**
3. **config.toml**

Example: `APP__PORT=3000` overrides `app.port` from TOML.

### Config sections

| Section | Description |
|---------|-------------|
| `[app]` | Title, host, port, workers, CORS, pagination |
| `[database]` | PostgreSQL: host, port, credentials + connection pool tuning |
| `[redis]` | Redis: host, port, password, pool size |
| `[s3]` | S3/MinIO: hosts (internal/external), keys, bucket |
| `[logging]` | Log level (DEBUG/INFO/WARNING/ERROR) |

## Architecture

```
src/
├── api/           — API layer (routes, dependencies)
├── core/          — Infrastructure (DB, cache, S3, config)
├── di/            — DI container (dishka)
├── models/        — SQLAlchemy models
├── repos/         — Repositories (sql/redis/s3)
├── services/      — Business logic
├── schemas/       — DTOs, enums, Pydantic schemas
└── utils/         — Utilities
```

### API layer (`src/api/`)

Each feature is organized as a set of files:

- **`routes/`** — routers with endpoints
- **`dependencies/`** — FastAPI dependencies
- **`schemas/`** — Pydantic request/response schemas

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

Three providers with different scopes:

| Provider | Scope | Provides |
|----------|-------|----------|
| `CoreProvider` | APP | AsyncEngine, session_factory, Redis pool, Redis client, Logger |
| `RequestProvider` | REQUEST | S3 clients (internal/external) |
| `RepositoryProvider` | REQUEST | AsyncSession, repositories |
| `ServiceProvider` | REQUEST | Business logic services |

APP scope — singletons for the entire app lifetime. REQUEST scope — new instance per HTTP request.

### Repositories

Abstract interfaces for the infrastructure layer (swappable in tests):

- **`AbstractBaseRepository[ModelT]`** — SQL CRUD (get_by_id, get_all, create, update, delete)
- **`AbstractCacheRepository`** — cache (get, set, delete, exists, get_many, set_many)
- **`AbstractS3Repository`** — files (upload, download, delete, exists, presigned_url)

### Models & mixins

- **`TimestampMixin`** — automatic `created_at` / `updated_at`
- **`SoftDeleteMixin`** — soft delete (`deleted_at`), automatic SELECT filtering

```python
class User(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(unique=True)
```

### Middleware

- **`HTTPLoggingMiddleware`** — HTTP request logging (path, method, status, duration)
- **`CORSMiddleware`** — CORS headers
- **`GZipMiddleware`** — response compression

### Error handling

Centralized exception handlers for:
- `ValueError`, `HTTPStatusError`, `RequestError`
- `IntegrityError`, `UniqueViolationError`
- `PyJWTError`
- Generic `Exception`

## Docker

```bash
docker build -t my-api .
docker run --env-file .env -p 8000:8000 my-api
```

Dockerfile: multi-stage build, non-root user, automatic migrations on startup.

## CI/CD (GitHub Actions)

| Workflow | Trigger | Action |
|----------|---------|--------|
| `tests.yml` | push/PR | pytest |
| `lint.yml` | push/PR | ruff |
| `typecheck.yml` | push/PR | ty |
| `dev.yml` | push to dev | Deploy to dev server |
| `main.yml` | push to main | Deploy to production |

## Make targets

```bash
make run              # Start server
make format           # Format code (ruff)
make lint             # Check code (ruff)
make revision         # Create alembic migration
make upgrade          # Apply migrations
make test             # Unit tests
make test/coverage    # Tests with coverage report
```
