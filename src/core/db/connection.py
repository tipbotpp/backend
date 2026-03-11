from sqlalchemy import event
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine, AsyncSession, AsyncEngine

from src.core.config import cfg
from src.core.db.soft_delete import filter_soft_deleted


def create_engine() -> AsyncEngine:
	"""
	Создает async engine для PostgreSQL.
	Живет на весь lifecycle приложения.
	"""
	return create_async_engine(
		url=cfg.database.async_database_url,
		echo=cfg.database.echo,
		pool_size=cfg.database.pool_size,
		max_overflow=cfg.database.max_overflow,
		pool_pre_ping=cfg.database.pool_pre_ping,
		pool_recycle=cfg.database.pool_recycle,
		pool_use_lifo=cfg.database.pool_use_lifo,
		pool_timeout=cfg.database.pool_timeout,
		connect_args={"ssl": False},
	)


def create_session_factory(
	engine: AsyncEngine,
) -> async_sessionmaker[AsyncSession]:
	"""
	Создает фабрику сессий.
	Используется для создания новых сессий на каждый запрос.
	"""
	factory = async_sessionmaker(
		bind=engine,
		class_=AsyncSession,
		expire_on_commit=False,
		autoflush=False,
		autocommit=False,
	)
	event.listen(factory.class_, "do_orm_execute", filter_soft_deleted)
	return factory

