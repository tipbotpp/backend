from redis.asyncio import ConnectionPool, Redis

from src.core.configs import cfg


def create_redis_pool() -> ConnectionPool:
	"""
	Создает connection pool для Redis.
	Аналог create_engine для SQLAlchemy.
	"""
	return ConnectionPool(
		host=cfg.redis.host,
		port=cfg.redis.port,
		db=cfg.redis.db,
		password=cfg.redis.password if cfg.redis.password else None,
		max_connections=cfg.redis.max_connections,
		socket_timeout=cfg.redis.socket_timeout,
		socket_connect_timeout=cfg.redis.socket_connect_timeout,
		decode_responses=True,
	)


async def create_redis_client(pool: ConnectionPool) -> Redis:
	"""
	Создает Redis клиент из pool.
	"""
	return Redis(connection_pool=pool)
