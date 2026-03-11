from collections.abc import Callable
from typing import Any, ClassVar, TypeVar

from sqlalchemy import (
	CheckConstraint,
	ForeignKeyConstraint,
	Index,
	PrimaryKeyConstraint,
	UniqueConstraint,
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase, declared_attr
from sqlalchemy.schema import Constraint

from src.schemas.dataclasses import ConstraintInfoDTO, IndexInfoDTO

T = TypeVar("T", bound="Base")


class Base(DeclarativeBase):
	TABLE_NAME: ClassVar[str]

	@declared_attr
	def __tablename__(cls) -> str:
		table_name_value = cls.__dict__.get("TABLE_NAME")
		if table_name_value and isinstance(table_name_value, str):
			return table_name_value

		tablename_attr = cls.__dict__.get("__tablename__")
		if tablename_attr and isinstance(tablename_attr, str):
			return tablename_attr

		return cls.__name__.lower()

	def __init_subclass__(cls, **kwargs: Any) -> None:
		"""Автоматически собирает индексы и constraints при создании подкласса."""
		super().__init_subclass__(**kwargs)

		if (
			"TABLE_NAME" in cls.__dict__
			and isinstance(cls.__dict__["TABLE_NAME"], str)
			and "__tablename__" in cls.__dict__
			and isinstance(cls.__dict__["__tablename__"], str)
		):
			delattr(cls, "__tablename__")

		if "TABLE_NAME" not in cls.__dict__:
			tablename_attr = cls.__dict__.get("__tablename__")
			if tablename_attr:
				if isinstance(tablename_attr, str):
					cls.TABLE_NAME = tablename_attr
				elif hasattr(tablename_attr, "fget"):
					cls.TABLE_NAME = tablename_attr.fget(cls)
			else:
				cls.TABLE_NAME = cls.__name__.lower()

		def _make_index_elements(index: Index) -> Callable[[], list[str]]:
			def index_elements() -> list[str]:
				return [
					col.name if hasattr(col, "name") else str(col)
					for col in index.expressions
				]

			return index_elements

		# Собираем автоматические индексы и constraints
		collected_items = []
		for name, attr in cls.__dict__.items():
			if not name.startswith("_") and (
				(name.endswith("_INDEX") and isinstance(attr, Index))
				or (
					name.endswith("_CONSTRAINT")
					and isinstance(attr, Constraint)
				)
			):
				if name.endswith("_INDEX") and isinstance(attr, Index):
					attr.index_elements = _make_index_elements(attr)
				collected_items.append(attr)

		# Если нет автоматических элементов, ничего не делаем
		if not collected_items:
			return

		# Получаем существующий __table_args__
		existing_table_args = getattr(cls, "__table_args__", None)
		existing_args = {}
		existing_items = []

		if existing_table_args:
			if isinstance(existing_table_args, dict):
				existing_args.update(existing_table_args)
			elif isinstance(existing_table_args, tuple):
				for arg in existing_table_args:
					if isinstance(arg, dict):
						existing_args.update(arg)
					elif not isinstance(arg, (Index, Constraint)):
						existing_items.append(arg)

		# Объединяем всё вместе
		all_items = collected_items + existing_items

		if existing_args:
			cls.__table_args__ = tuple(all_items) + (existing_args,)
		elif all_items:
			cls.__table_args__ = tuple(all_items)

	@classmethod
	def get_indexes(cls) -> dict[str, IndexInfoDTO]:
		"""Возвращает информацию о всех индексах класса."""
		indexes = {}
		for name, attr in cls.__dict__.items():
			if (
				name.endswith("_INDEX")
				and not name.startswith("_")
				and isinstance(attr, Index)
			):
				indexes[name] = IndexInfoDTO(
					index=attr,
					name=attr.name,
					unique=attr.unique,
					columns=[str(col) for col in attr.columns],
					expressions=list(attr.expressions),
					dialect_kwargs=dict(attr.dialect_kwargs),
					dialect_options=dict(attr.dialect_options),
					postgresql_where=attr.dialect_options.get(
						"postgresql",
						{},
					).get(
						"where",
					),
					postgresql_using=attr.dialect_options.get(
						"postgresql",
						{},
					).get(
						"using",
					),
				)
		return indexes

	@classmethod
	def get_index_attr_name(cls, index: Index) -> str | None:
		"""Получить имя атрибута класса по объекту Index."""
		for name, attr in cls.__dict__.items():
			if (
				name.endswith("_INDEX")
				and not name.startswith("_")
				and isinstance(attr, Index)
				and attr is index
			):
				return name
		return None

	@classmethod
	def get_index_elements(
		cls,
		index_name: str | Index,
	) -> IndexInfoDTO | None:
		"""Получить элементы конкретного индекса."""
		if isinstance(index_name, Index):
			attr_name = cls.get_index_attr_name(index_name)
			if not attr_name:
				return None
			index_name = attr_name

		if not index_name.endswith("_INDEX"):
			index_name = f"{index_name}_INDEX"

		attr = getattr(cls, index_name, None)
		if not isinstance(attr, Index):
			return None

		return IndexInfoDTO(
			index=attr,
			name=attr.name,
			unique=attr.unique,
			columns=[str(col) for col in attr.columns],
			expressions=list(attr.expressions),
			dialect_kwargs=dict(attr.dialect_kwargs),
			dialect_options=dict(attr.dialect_options),
			postgresql_where=attr.dialect_options.get("postgresql", {}).get(
				"where",
			),
			postgresql_using=attr.dialect_options.get("postgresql", {}).get(
				"using",
			),
		)

	@classmethod
	def get_constraints(cls) -> dict[str, ConstraintInfoDTO]:
		"""Возвращает информацию о всех constraints класса."""
		constraints = {}
		for name, attr in cls.__dict__.items():
			if (
				name.endswith("_CONSTRAINT")
				and not name.startswith("_")
				and isinstance(attr, Constraint)
			):
				sqltext = None
				columns = None
				referred_table = None

				if isinstance(attr, CheckConstraint):
					sqltext = (
						str(attr.sqltext) if hasattr(attr, "sqltext") else None
					)
				elif isinstance(
					attr,
					(
						UniqueConstraint,
						ForeignKeyConstraint,
						PrimaryKeyConstraint,
					),
				):
					if hasattr(attr, "columns"):
						columns = [str(col) for col in attr.columns]
					if isinstance(attr, ForeignKeyConstraint) and hasattr(
						attr,
						"referred_table",
					):
						referred_table = str(attr.referred_table)

				constraints[name] = ConstraintInfoDTO(
					constraint=attr,
					name=attr.name,
					type=type(attr).__name__,
					dialect_kwargs=dict(attr.dialect_kwargs),
					dialect_options=dict(attr.dialect_options),
					sqltext=sqltext,
					columns=columns,
					referred_table=referred_table,
				)
		return constraints

	@classmethod
	def get_constraint_elements(
		cls,
		constraint_name: str,
	) -> ConstraintInfoDTO | None:
		"""Получить элементы конкретного constraint."""
		if not constraint_name.endswith("_CONSTRAINT"):
			constraint_name = f"{constraint_name}_CONSTRAINT"

		attr = getattr(cls, constraint_name, None)
		if not isinstance(attr, Constraint):
			return None

		sqltext = None
		columns = None
		referred_table = None

		if isinstance(attr, CheckConstraint):
			sqltext = str(attr.sqltext) if hasattr(attr, "sqltext") else None
		elif isinstance(
			attr,
			(UniqueConstraint, ForeignKeyConstraint, PrimaryKeyConstraint),
		):
			if hasattr(attr, "columns"):
				columns = [str(col) for col in attr.columns]
			if isinstance(attr, ForeignKeyConstraint) and hasattr(
				attr,
				"referred_table",
			):
				referred_table = str(attr.referred_table)

		return ConstraintInfoDTO(
			constraint=attr,
			name=attr.name,
			type=type(attr).__name__,
			dialect_kwargs=dict(attr.dialect_kwargs),
			dialect_options=dict(attr.dialect_options),
			sqltext=sqltext,
			columns=columns,
			referred_table=referred_table,
		)

	def to_dict(self) -> dict[str, Any]:
		"""Преобразует объект модели в словарь, используя столбцы таблицы."""
		return {
			column.name: getattr(self, column.name)
			for column in self.__table__.columns
		}

	def update(self: T, **kwargs) -> T:  # noqa: ANN003
		"""Обновляет атрибуты объекта на основе переданных именованных аргументов."""
		for key, value in kwargs.items():
			if hasattr(self, key):
				setattr(self, key, value)
		return self

	async def save(self: T, session: AsyncSession) -> T:
		"""
		Добавляет объект в сессию.

		Commit выполняется автоматически зависимостью FastAPI.
		Не выполняет commit и refresh - это делает dependency injection.
		"""
		session.add(self)
		return self

	async def delete(self, session: AsyncSession) -> None:
		"""
		Помечает объект для удаления из сессии.

		Commit выполняется автоматически зависимостью FastAPI.
		Не выполняет commit - это делает dependency injection.
		"""
		session.delete(self)

	@classmethod
	async def get_by_id(cls: type[T], session: AsyncSession, id: Any) -> T | None:
		"""Асинхронно возвращает объект по первичному ключу (id)."""
		return await session.get(cls, id)

	@classmethod
	def from_dict(cls: type[T], data: dict[str, Any]) -> T:
		"""Создает экземпляр модели на основе словаря."""
		return cls(**data)
