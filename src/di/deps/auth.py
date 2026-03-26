from typing import TypeAlias

from dishka.integrations.fastapi import FromDishka

from src.schemas.dataclasses.users import UserDTO

CurrentUserDep: TypeAlias = FromDishka[UserDTO]
