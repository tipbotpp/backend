from __future__ import annotations

from dishka.integrations.fastapi import DishkaRoute, FromDishka, inject
from fastapi import APIRouter
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exc.exceptions import InvalidRoleError, RoleAlreadySetError
from src.di.deps.auth import CurrentUserDep
from src.repos import sql
from src.schemas.enums.users import UserRole
from src.schemas.pydantic import users as users_schema
from src.utils.mappers import map_model

router = APIRouter(prefix="/users", route_class=DishkaRoute)

_VIEWER_START_BALANCE = 100


@router.get("/me", response_model=users_schema.UserResponse)
@inject
async def get_me(
	user: CurrentUserDep,
) -> users_schema.UserResponse:
	return map_model(user, users_schema.UserResponse)


@router.patch("/me/role", response_model=users_schema.UserRoleResponse)
@inject
async def set_role(
	body: users_schema.UserRoleBody,
	session: FromDishka[AsyncSession],
	user: CurrentUserDep,
) -> users_schema.UserRoleResponse:
	"""
	Выбор роли. Разрешён только один раз (пока роль = null).
	Viewer получает 100 стартовых монет.
	"""
	if user.role is not None:
		raise RoleAlreadySetError

	try:
		role = UserRole(body.role)
	except ValueError:
		raise InvalidRoleError

	new_balance = _VIEWER_START_BALANCE if role is UserRole.VIEWER else None

	updated = await sql.users_repo.update_role(
		session,
		user.telegram_id,
		role.value,
		balance=new_balance,
	)

	return map_model(updated, users_schema.UserRoleResponse)
