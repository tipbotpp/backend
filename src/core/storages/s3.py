from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from aiobotocore.session import get_session
from botocore.config import Config

from src.core.config import cfg


@asynccontextmanager
async def get_s3_client() -> AsyncIterator[Any]:
	"""
	Создает S3 клиент для внутреннего использования.
	Аналог create_engine для SQLAlchemy.
	"""
	session = get_session()
	config = Config(
		region_name=cfg.s3.aws_region,
		retries={"max_attempts": 3, "mode": "adaptive"},
		max_pool_connections=50,
		connect_timeout=60,
		read_timeout=60,
	)

	async with session.create_client(
		"s3",
		endpoint_url=cfg.s3.internal_host,
		aws_access_key_id=cfg.s3.aws_access_key,
		aws_secret_access_key=cfg.s3.aws_secret_access_key,
		config=config,
	) as client:
		yield client


@asynccontextmanager
async def get_s3_external_client() -> AsyncIterator[Any]:
	"""
	Создает S3 клиент для внешних URL (presigned).
	"""
	session = get_session()
	async with session.create_client(
		"s3",
		region_name=cfg.s3.aws_region,
		aws_secret_access_key=cfg.s3.aws_secret_access_key,
		aws_access_key_id=cfg.s3.aws_secret_access_key,
		endpoint_url=cfg.s3.external_host,
	) as client:
		yield client