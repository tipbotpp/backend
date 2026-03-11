from typing import Any, Generic, Self, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class BaseSchema(BaseModel):
	def to_dict(self, **kwargs: Any) -> dict[str, Any]:
		"""
		Возвращает словарь данных модели.
		По умолчанию исключает поля со значением None.
		"""
		return self.model_dump(exclude_none=True, **kwargs)

	def update(self, **kwargs: Any) -> Self:
		"""
		Возвращает новый экземпляр модели с обновлёнными полями.
		Использует метод copy() от Pydantic.
		"""
		return self.model_copy(update=kwargs)

	def __str__(self) -> str:
		"""
		Возвращает форматированное JSON-представление модели для удобного чтения.
		"""
		return self.model_dump_json(indent=2)

	class Config:
		from_attributes = True
		populate_by_name = True


class Paginated(BaseModel, Generic[T]):  # noqa: UP046
	items: list[T]
	total: int
	limit: int
	offset: int


# class PaginationRequest(BaseSchema):
# 	limit: int = Query(cfg.app.default_limit, ge=1, le=100, description="Количество элементов")
# 	offset: int = Query(cfg.app.default_offset, ge=0, description="Смещение")
