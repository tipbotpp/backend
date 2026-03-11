import mimetypes
from typing import Any
from .interfaces import AbstractS3Repository


class PhotoRepository(AbstractS3Repository):
	"""Реализация репозитория фотографий на S3."""

	def __init__(self, s3_client: Any, bucket: str) -> None:
		self.client = s3_client
		self.bucket = bucket

	async def upload_file(
		self,
		file_data: bytes,
		file_id: str,
	) -> None:
		content_type = self._detect_content_type(file_id)

		await self.client.put_object(
			Bucket=self.bucket,
			Key=file_id,
			Body=file_data,
			ContentType=content_type,
		)

	async def download_file(self, file_id: str) -> bytes:
		response = await self.client.get_object(
			Bucket=self.bucket,
			Key=file_id,
		)
		async with response["Body"] as stream:
			return await stream.read()

	async def delete_file(self, file_id: str) -> None:
		await self.client.delete_object(
			Bucket=self.bucket,
			Key=file_id,
		)

	async def exists(self, file_id: str) -> bool:
		try:
			await self.client.head_object(
				Bucket=self.bucket,
				Key=file_id,
			)
			return True
		except Exception:
			return False

	async def generate_presigned_url(
		self,
		file_id: str,
		expires_in: int = 3600,
	) -> str:
		return await self.client.generate_presigned_url(
			ClientMethod="get_object",
			Params={"Bucket": self.bucket, "Key": file_id},
			ExpiresIn=expires_in,
		)

	@staticmethod
	def _detect_content_type(filename: str) -> str:
		content_type, _ = mimetypes.guess_type(filename)
		return content_type or "application/octet-stream"