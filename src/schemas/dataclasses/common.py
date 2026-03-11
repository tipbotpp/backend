from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class PaginationDTO:
	"""DTO для параметров пагинации limit/offset."""

	limit: int
	offset: int


@dataclass(slots=True)
class PaginatedDTO[T]:
	"""Generic DTO для пагинированного ответа."""

	items: list[T]
	total: int
	limit: int
	offset: int
