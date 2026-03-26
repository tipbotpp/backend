from typing import Annotated, TypeAlias

from fastapi import Depends

from src.schemas.dataclasses.common import PaginationDTO
from src.schemas.pydantic.common import PaginationFilters


def _pagination(
	params: Annotated[PaginationFilters, Depends()],
) -> PaginationDTO:
	return PaginationDTO(limit=params.limit, offset=params.offset)


PaginationDep: TypeAlias = Annotated[PaginationDTO, Depends(_pagination)]
