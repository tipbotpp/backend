from src.core.configs import cfg
from src.core.storages import S3Manager


async def resolve_presigned_url(manager: S3Manager, raw_key: str | None) -> str | None:
	"""Превращает S3-ключ в presigned URL. None → None."""
	if not raw_key:
		return None
	return await manager.generate_presigned_url(cfg.s3.aws_bucket, raw_key)
