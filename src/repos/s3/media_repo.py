from src.core.storages import S3Manager


def parse_s3_key(raw: str) -> tuple[str, str]:
	"""
	Парсит ключ формата "{bucket}/{key}" в (bucket, key).
	ML-сервис возвращает именно такой формат.
	"""
	bucket, _, key = raw.partition("/")
	return bucket, key


async def resolve_presigned_url(
	manager: S3Manager,
	raw_key: str | None,
) -> str | None:
	"""Превращает S3-ключ в presigned URL. None → None."""
	if not raw_key:
		return None
	bucket, key = parse_s3_key(raw_key)
	return await manager.generate_presigned_url(bucket, key)
