from dishka import Provider, Scope, provide

from src.repos.sql.interfaces import AbstractBaseRepository
from src.repos.redis.interfaces import AbstractCacheRepository
from src.repos.s3.interfaces import AbstractS3Repository
from src.services.example import ExampleService


class ServiceProvider(Provider):
	scope = Scope.REQUEST

	@provide
	def get_example_service(
		self,
		sql_repo: AbstractBaseRepository,
		redis_repo: AbstractCacheRepository,
		s3_repo: AbstractS3Repository,
	) -> ExampleService:
		return ExampleService(sql_repo, redis_repo, s3_repo)
