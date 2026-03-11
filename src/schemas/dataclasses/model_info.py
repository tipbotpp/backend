from dataclasses import dataclass
from typing import Any

from sqlalchemy import Index
from sqlalchemy.schema import Constraint


@dataclass
class IndexInfoDTO:
	index: Index
	name: str | None
	unique: bool
	columns: list[str]
	expressions: list[Any]
	dialect_kwargs: dict[str, Any]
	dialect_options: dict[str, Any]
	postgresql_where: Any
	postgresql_using: Any


@dataclass
class ConstraintInfoDTO:
	constraint: Constraint
	name: str | None
	type: str
	dialect_kwargs: dict[str, Any]
	dialect_options: dict[str, Any]
	sqltext: str | None = None
	columns: list[str] | None = None
	referred_table: str | None = None
