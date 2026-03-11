# fastapi-template

Production-ready template for REST APIs built with FastAPI.

**[Documentation (EN)](docs/en/README.md)** | **[Документация (RU)](docs/ru/README.md)**

## Stack

| Layer | Tech |
|-------|------|
| Web framework | [FastAPI](https://fastapi.tiangolo.com/) |
| DI | [dishka](https://github.com/reagento/dishka) |
| ORM | [SQLAlchemy 2](https://docs.sqlalchemy.org/) + asyncpg |
| Migrations | [Alembic](https://alembic.sqlalchemy.org/) |
| Cache | [redis-py](https://github.com/redis/redis-py) (async) |
| Object storage | [aiobotocore](https://github.com/aio-libs/aiobotocore) (S3/MinIO) |
| Logging | [structlog](https://www.structlog.org/) (JSON) |
| Config | [pydantic-settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/) (TOML/JSON/.env) |
| Linter | [ruff](https://docs.astral.sh/ruff/) |
| Package manager | [uv](https://docs.astral.sh/uv/) |

## Quick start

```bash
# Clone
git clone https://github.com/your-repo/fastapi_template.git my-api
cd my-api

# Install
uv sync --dev

# Configure
cp config.example.toml config.toml
# edit config.toml

# Run
make run
```

## Project structure

```
src/
├── api/                  # API layer
│   ├── routes/           # Route handlers
│   ├── dependencies/     # FastAPI dependencies
│   └── schemas/          # Request/Response schemas
├── core/                 # Infrastructure
│   ├── config/           # Pydantic settings (TOML/JSON/.env)
│   ├── db/               # SQLAlchemy engine, session, soft delete
│   ├── cache/            # Redis connection pool
│   ├── storages/         # S3/MinIO client
│   ├── exc/              # Exception handlers
│   └── middlewares/      # HTTP logging middleware
├── di/                   # Dishka DI container & providers
├── models/               # SQLAlchemy models + mixins
├── repos/                # Repository pattern (sql/redis/s3)
├── services/             # Business logic
├── schemas/              # DTOs, enums, Pydantic schemas
└── utils/                # Helpers (datetime, mappers)
```

## Make targets

```bash
make run              # Start server
make format           # Format code (ruff)
make lint             # Check code (ruff)
make revision         # Create alembic migration
make upgrade          # Apply migrations
make test             # Run unit tests
make test/coverage    # Tests with coverage report
```

## License

MIT
