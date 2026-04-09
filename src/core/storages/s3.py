from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from aiobotocore.session import get_session
from botocore.config import Config

from src.core.configs import cfg


class S3Manager:
	"""
	Долгоживущий менеджер S3-соединений (Scope.APP).
	Используется только для генерации presigned URL —
	загрузку файлов выполняет ML-сервис напрямую.
	"""

	@asynccontextmanager
	async def _internal_client(self) -> AsyncIterator[Any]:
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
	async def _external_client(self) -> AsyncIterator[Any]:
		session = get_session()
		async with session.create_client(
			"s3",
			region_name=cfg.s3.aws_region,
			endpoint_url=cfg.s3.external_host,
			aws_access_key_id=cfg.s3.aws_access_key,
			aws_secret_access_key=cfg.s3.aws_secret_access_key,
		) as client:
			yield client

	async def generate_presigned_url(self, bucket: str, key: str) -> str:
		async with self._external_client() as client:
			return await client.generate_presigned_url(
				ClientMethod="get_object",
				Params={"Bucket": bucket, "Key": key},
				ExpiresIn=cfg.s3.presigned_url_ttl,
			)
