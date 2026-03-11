from redis.asyncio import Redis, ConnectionPool

from src.core.config import cfg


def create_redis_pool() -> ConnectionPool:
	"""
	Создает connection pool для Redis.
	Аналог create_engine для SQLAlchemy.
	"""
	return ConnectionPool(
		host=cfg.redis.redis_host,
		port=cfg.redis.redis_port,
		db=cfg.redis.redis_db,
		password=cfg.redis.redis_password if cfg.redis.redis_password else None,
		max_connections=cfg.redis.redis_max_connections,
		socket_timeout=cfg.redis.redis_socket_timeout,
		socket_connect_timeout=cfg.redis.redis_socket_connect_timeout,
		decode_responses=True,
	)


async def create_redis_client(pool: ConnectionPool) -> Redis:
	"""
	Создает Redis клиент из pool.
	"""
	return Redis(connection_pool=pool)