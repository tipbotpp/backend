import asyncio
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config
from src.core.configs import cfg
from src.models import (
	Base,  # все модели подтягиваются через src/models/__init__.py
)

alembic_cfg = context.config

# Логирование через alembic.ini если файл реально существует
if (
	alembic_cfg.config_file_name
	and Path(alembic_cfg.config_file_name).exists()
):
	fileConfig(alembic_cfg.config_file_name)

# URL берём из нашего конфига, не из alembic.ini
alembic_cfg.set_main_option("sqlalchemy.url", cfg.database.async_database_url)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
	url = alembic_cfg.get_main_option("sqlalchemy.url")
	context.configure(
		url=url,
		target_metadata=target_metadata,
		literal_binds=True,
		dialect_opts={"paramstyle": "named"},
	)
	with context.begin_transaction():
		context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
	context.configure(connection=connection, target_metadata=target_metadata)
	with context.begin_transaction():
		context.run_migrations()


async def run_async_migrations() -> None:
	connectable = async_engine_from_config(
		alembic_cfg.get_section(alembic_cfg.config_ini_section, {}),
		prefix="sqlalchemy.",
		poolclass=pool.NullPool,
	)
	async with connectable.connect() as connection:
		await connection.run_sync(do_run_migrations)
	await connectable.dispose()


def run_migrations_online() -> None:
	asyncio.run(run_async_migrations())


if context.is_offline_mode():
	run_migrations_offline()
else:
	run_migrations_online()
