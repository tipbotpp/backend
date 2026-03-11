from abc import ABC, abstractmethod


class AbstractS3Repository(ABC):
	"""Абстрактный интерфейс для работы с фотографиями."""

	@abstractmethod
	async def upload_file(
		self,
		file_data: bytes,
		file_id: str,
	) -> None:
		"""Загружает фото в хранилище."""
		raise NotImplementedError

	@abstractmethod
	async def download_file(self, file_id: str) -> bytes:
		"""Скачивает фото из хранилища."""
		raise NotImplementedError

	@abstractmethod
	async def delete_file(self, file_id: str) -> None:
		"""Удаляет фото из хранилища."""
		raise NotImplementedError

	@abstractmethod
	async def exists(self, file_id: str) -> bool:
		"""Проверяет существование файла."""
		raise NotImplementedError

	@abstractmethod
	async def generate_presigned_url(
		self,
		file_id: str,
		expires_in: int = 3600,
	) -> str:
		"""Генерирует временную ссылку на файл."""
		raise NotImplementedError
