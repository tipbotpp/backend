from src.models.user import User
from src.repos.redis.interfaces import AbstractCacheRepository
from src.repos.s3.interfaces import AbstractS3Repository
from src.repos.sql.interfaces import AbstractBaseRepository


class ExampleService:
	def __init__(
		self,
		sql_repo: AbstractBaseRepository,
		redis_repo: AbstractCacheRepository,
		s3_repo: AbstractS3Repository,
	) -> None:
		self.sql_repo = sql_repo
		self.cache = redis_repo
		self.photos = s3_repo

	async def get_user_with_cache(
		self,
		user_id: int,
	) -> User | None:
		# Проверяем кеш
		cache_key = f"user:{user_id}"
		cached = await self.cache.get(cache_key)

		if cached:
			# TODO: десериализовать из JSON
			pass

		# Идем в БД
		user = await self.sql_repo.get_by_id(user_id)

		if user:
			# Кешируем на 5 минут
			# TODO: сериализовать в JSON
			await self.cache.set(cache_key, "{}", ttl=300)

		return user

	async def create_user_with_photo(
		self,
		email: str,
		first_name: str,
		photo_data: bytes,
	) -> User:
		# Создаем пользователя
		user = await self.sql_repo.create(
			email=email,
			first_name=first_name,
		)

		# Загружаем фото
		photo_id = f"users/{user.id}/photo.jpg"
		await self.photos.upload_file(photo_data, photo_id)

		return user

	async def invalidate_user_cache(self, user_id: int) -> None:
		cache_key = f"user:{user_id}"
		await self.cache.delete(cache_key)
