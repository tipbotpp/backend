# ruff: noqa: PLR0911, UP047
from __future__ import annotations

from dataclasses import asdict, is_dataclass
from typing import Any, TypeVar, get_args, get_origin, get_type_hints

from pydantic import BaseModel

T = TypeVar("T")
U = TypeVar("U")


def map_value(value: Any, target_type: type[Any]) -> Any:
    """
    Рекурсивное приведение value к target_type для вложенных структур.

    Поддерживает:
    - Optional[T] / Union[T, None]
    - list[T] / set[T] / tuple[T]
    - dataclass / pydantic как вложенные типы
    - примитивы (int, str, bool, и т.п.) — возвращаются как есть
    """
    if value is None:
        return None

    # Any — ничего не делаем
    if target_type is Any:
        return value

    origin = get_origin(target_type)
    args = get_args(target_type)

    # Optional[T] / Union[T, None]
    if origin is not None and origin is not tuple and type(None) in args:
        # берем первый не-None тип
        inner_types = [t for t in args if t is not type(None)]
        inner_type = inner_types[0] if inner_types else Any
        return map_value(value, inner_type)

    # list[T]
    if origin in (list, list[Any]):
        (inner_type,) = args or (Any,)
        return [map_value(v, inner_type) for v in (value or [])]

    # set[T]
    if origin is set:
        (inner_type,) = args or (Any,)
        return {map_value(v, inner_type) for v in (value or set())}

    # tuple[T, ...]
    if origin is tuple:
        if len(args) == 2 and args[1] is Ellipsis:
            (inner_type,) = args[:1]
            return tuple(map_value(v, inner_type) for v in (value or ()))
        # кортеж фиксированной длины — поэлементно
        return tuple(
            map_value(v, t) for v, t in zip(value, args, strict=False)
        )

    # dict[K, V] — обычно оставляем как есть (при желании можем маппить значения)
    if origin is dict:
        # если очень хочется, можно тут добавить рекурсивный маппинг values
        return value

    # вложенный dataclass / pydantic
    try:
        if is_dataclass(target_type) or issubclass(target_type, BaseModel):
            # тут используем общий map_model, но этот вызов
            # уже будет работать с одним вложенным объектом
            return map_model(value, target_type)
    except TypeError:
        # issubclass на неприменимых типах кидает TypeError — просто игнорим
        pass

    # для примитивов/прочего — просто возвращаем как есть, не кастим
    return value


def map_model(source: Any, target_type: type[U]) -> U:
    """
    Универсальный маппер для сущностей вида ORM / DTO / Pydantic с поддержкой вложенности.

    Примеры:
    - orm -> dto:
        user_dto = map_model(user_orm, UserDTO)

    - dto -> pydantic:
        user_schema = map_model(user_dto, UserResponse)

    - orm -> pydantic:
        user_schema = map_model(user_orm, UserResponse)

    Работает в два шага:
    1) превращает source в dict (учитывая тип: pydantic / dataclass / orm / dict)
    2) фильтрует поля по аннотациям target_type и рекурсивно маппит значения
    """

    if source is None:
        raise ValueError("map_model: source cannot be None")

    # 1. приводим source к dict
    if isinstance(source, BaseModel):
        data = source.model_dump(exclude_unset=True)

    elif is_dataclass(source):
        data = asdict(source)

    elif isinstance(source, dict):
        data = source

    elif hasattr(source, "__dict__"):
        # orm / обычный объект — берем только непубличные атрибуты
        data = {
            k: v
            for k, v in vars(source).items()
            if not k.startswith("_")
        }

    else:
        raise TypeError(f"map_model: unsupported source type {type(source)}")

    # 2. достаем аннотации таргета
    type_hints = get_type_hints(target_type)

    # 3. собираем словарь для таргета с учетом вложенных типов
    mapped_data: dict[str, Any] = {}

    for field_name, field_type in type_hints.items():
        if field_name not in data:
            continue

        raw_value = data[field_name]
        mapped_data[field_name] = map_value(raw_value, field_type)

    # 4. создаем таргет
    return target_type(**mapped_data)
