from __future__ import annotations

from typing import Annotated

from dishka.integrations.fastapi import DishkaRoute, FromDishka, inject
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exc.exceptions import (
	InvalidRoleError,
	NotFoundError,
	RoleAlreadySetError,
)
from src.di.deps.auth import CurrentUserDep
from src.repos import sql
from src.schemas.enums.users import UserRole
from src.schemas.pydantic import users as users_schema
from src.services.logger import get_logger
from src.utils.mappers import map_model

router = APIRouter(prefix="/users", route_class=DishkaRoute)

logger = get_logger().bind(layer="endpoint", module="users")

_VIEWER_START_BALANCE = 100


@router.get(
	"/me",
	response_model=users_schema.UserResponse,
	summary="Профиль текущего пользователя",
)
@inject
async def get_me(user: CurrentUserDep) -> users_schema.UserResponse:
	"""Возвращает полный профиль аутентифицированного пользователя.

	Returns:
	    UserResponse: Профиль с ролью, балансом и датой регистрации.

	Raises:
	    401: Пользователь не аутентифицирован.
	"""
	log = logger.bind(request_user_id=user.telegram_id)
	log.debug("GET /users/me", role=user.role)
	return map_model(user, users_schema.UserResponse)


@router.patch(
	"/me",
	response_model=users_schema.UserResponse,
	summary="Обновить профиль (имя, описание)",
)
@inject
async def update_me(
	body: users_schema.UserUpdateBody,
	session: FromDishka[AsyncSession],
	user: CurrentUserDep,
) -> users_schema.UserResponse:
	"""Обновляет отображаемое имя и/или описание профиля.

	Все поля опциональны — передавай только то, что нужно изменить.
	После установки `display_name` через этот эндпоинт имя перестаёт
	синхронизироваться из Telegram.

	Args:
	    body: Новое отображаемое имя (до 64 символов) и/или описание (до 500 символов).

	Returns:
	    UserResponse: Обновлённый профиль.

	Raises:
	    401: Пользователь не аутентифицирован.
	    422: Превышена максимальная длина поля.
	"""
	log = logger.bind(request_user_id=user.telegram_id)
	log.debug("PATCH /users/me")
	updated = await sql.users_repo.update_profile_custom(
		session,
		user.telegram_id,
		display_name=body.display_name,
		description=body.description,
	)
	log.info("profile updated")
	return map_model(updated, users_schema.UserResponse)


@router.patch(
	"/me/role",
	response_model=users_schema.UserRoleResponse,
	summary="Установить роль (viewer / streamer) — только один раз",
)
@inject
async def set_role(
	body: users_schema.UserRoleBody,
	session: FromDishka[AsyncSession],
	user: CurrentUserDep,
) -> users_schema.UserRoleResponse:
	"""Устанавливает роль пользователя. Вызывается ровно один раз после регистрации.

	При выборе роли `viewer` начисляется стартовый баланс 100 монет.
	После установки роль изменить невозможно.

	Args:
	    body: Желаемая роль: `viewer` или `streamer`.

	Returns:
	    UserRoleResponse: Установленная роль и актуальный баланс.

	Raises:
	    401: Пользователь не аутентифицирован.
	    409: Роль уже установлена ранее.
	    422: Неизвестное значение роли (допустимо только viewer | streamer).
	"""
	log = logger.bind(request_user_id=user.telegram_id, request_role=body.role)
	log.debug("PATCH /users/me/role")

	if user.role is not None:
		log.error("role already set", current_role=user.role)
		raise RoleAlreadySetError

	try:
		role = UserRole(body.role)
	except ValueError:
		log.error("invalid role value", request_role=body.role)
		raise InvalidRoleError

	new_balance = _VIEWER_START_BALANCE if role is UserRole.VIEWER else None

	updated = await sql.users_repo.update_role(
		session,
		user.telegram_id,
		role.value,
		balance=new_balance,
	)

	log.info("role set", role=role.value, start_balance=new_balance)
	return map_model(updated, users_schema.UserRoleResponse)


@router.get(
	"/streamers",
	response_model=users_schema.StreamerListResponse,
	summary="Список стримеров с активным стримом",
)
@inject
async def get_streamers(
	filters: Annotated[users_schema.StreamerFilters, Depends()],
	session: FromDishka[AsyncSession],
	user: CurrentUserDep,
) -> users_schema.StreamerListResponse:
	"""Возвращает постраничный список стримеров, у которых прямо сейчас идёт стрим.

	Поддерживает поиск по username и отображаемому имени.
	Для каждого стримера возвращается превью текущей цели сбора (если задана).

	Args:
	    filters: Параметры поиска и пагинации (search, limit, offset).

	Returns:
	    StreamerListResponse: Список стримеров с пагинацией.

	Raises:
	    401: Пользователь не аутентифицирован.
	"""
	log = logger.bind(
		request_user_id=user.telegram_id,
		request_search=filters.search,
	)
	log.debug("GET /users/streamers")

	streamers, total = await sql.users_repo.get_active_streamers(
		session,
		search=filters.search,
		limit=filters.limit,
		offset=filters.offset,
	)

	if not streamers:
		return users_schema.StreamerListResponse(
			items=[],
			total=0,
			limit=filters.limit,
			offset=filters.offset,
		)

	streamer_ids = [s.telegram_id for s in streamers]
	goals = await sql.stream_goals_repo.get_by_streamer_ids(
		session,
		streamer_ids,
	)
	goal_map = {g.streamer_id: g for g in goals}

	items = [
		users_schema.StreamerItemResponse(
			telegram_id=s.telegram_id,
			username=s.username,
			display_name=s.display_name,
			avatar_url=s.avatar_url,
			is_live=True,
			goal=(
				users_schema.GoalPreview(
					title=goal_map[s.telegram_id].title,
					target_amount=goal_map[s.telegram_id].target_amount,
					current_amount=goal_map[s.telegram_id].current_amount,
				)
				if s.telegram_id in goal_map
				else None
			),
		)
		for s in streamers
	]

	log.info("streamers retrieved", total=total)
	return users_schema.StreamerListResponse(
		items=items,
		total=total,
		limit=filters.limit,
		offset=filters.offset,
	)


@router.get(
	"/{user_id}",
	response_model=users_schema.StreamerProfileResponse,
	summary="Публичный профиль стримера",
)
@inject
async def get_streamer_profile(
	user_id: int,
	session: FromDishka[AsyncSession],
	user: CurrentUserDep,
) -> users_schema.StreamerProfileResponse:
	"""Возвращает публичный профиль пользователя по его Telegram ID.

	Включает статус стрима, текущую цель сбора и превью настроек алерта
	(цвета, шрифт, длительность) для отображения на странице стримера.

	Args:
	    user_id: Telegram ID пользователя.

	Returns:
	    StreamerProfileResponse: Публичный профиль с целью и превью алерта.

	Raises:
	    401: Пользователь не аутентифицирован.
	    404: Пользователь с указанным ID не найден.
	"""
	log = logger.bind(request_user_id=user.telegram_id, target_user_id=user_id)
	log.debug("GET /users/{user_id}")

	target = await sql.users_repo.get_by_telegram_id(session, user_id)
	if target is None:
		raise NotFoundError()

	active_session = await sql.stream_sessions_repo.get_active_by_streamer_id(
		session,
		user_id,
	)
	is_live = active_session is not None

	goal = await sql.stream_goals_repo.get_by_streamer_id(session, user_id)
	alert = await sql.alert_settings_repo.get_by_streamer_id(session, user_id)

	log.info("streamer profile retrieved", is_live=is_live)
	return users_schema.StreamerProfileResponse(
		telegram_id=target.telegram_id,
		username=target.username,
		display_name=target.display_name,
		avatar_url=target.avatar_url,
		description=target.description,
		is_live=is_live,
		goal=(
			users_schema.GoalPreview(
				title=goal.title,
				target_amount=goal.target_amount,
				current_amount=goal.current_amount,
			)
			if goal
			else None
		),
		alert_preview=(
			users_schema.AlertPreview(
				bg_color=alert.bg_color,
				text_color=alert.text_color,
				font=alert.font,
				duration_sec=alert.duration_sec,
			)
			if alert
			else None
		),
	)
