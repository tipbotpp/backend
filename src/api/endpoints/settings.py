from __future__ import annotations

from dishka.integrations.fastapi import DishkaRoute, FromDishka, inject
from fastapi import APIRouter, status

from src.di.deps.auth import CurrentUserDep
from src.schemas.pydantic import settings as settings_schema
from src.services.logger import get_logger
from src.services.settings import SettingsService

router = APIRouter(prefix="/settings", route_class=DishkaRoute)

logger = get_logger().bind(layer="endpoint", module="settings")


# ── Alert Style ───────────────────────────────────────────────────────────────

@router.get("/alert", response_model=settings_schema.AlertSettingsResponse, summary="Настройки алерта стримера")
@inject
async def get_alert(
	user: CurrentUserDep,
	settings_service: FromDishka[SettingsService],
) -> settings_schema.AlertSettingsResponse:
	"""Возвращает текущие настройки OBS-алерта стримера.

	Если настройки ещё не созданы — автоматически создаются со значениями по умолчанию.

	Returns:
		AlertSettingsResponse: Цвета, шрифт, длительность и флаги TTS/изображения.

	Raises:
		401: Пользователь не аутентифицирован.
		403: Доступно только стримерам.
	"""
	log = logger.bind(request_user_id=user.telegram_id)
	log.debug("GET /settings/alert")
	result = await settings_service.get_alert(user)
	return settings_schema.AlertSettingsResponse(
		bg_color=result.bg_color,
		text_color=result.text_color,
		font=result.font,
		duration_sec=result.duration_sec,
		image_enabled=result.image_enabled,
		tts_enabled=result.tts_enabled,
		tts_voice=result.tts_voice,
	)


@router.patch("/alert", response_model=settings_schema.AlertSettingsResponse, summary="Обновить настройки алерта")
@inject
async def update_alert(
	body: settings_schema.AlertSettingsBody,
	user: CurrentUserDep,
	settings_service: FromDishka[SettingsService],
) -> settings_schema.AlertSettingsResponse:
	"""Обновляет настройки OBS-алерта. Все поля опциональны — меняй только нужные.

	Цвета передаются строго в формате `#RRGGBB`. Длительность алерта от 1 до 30 секунд.

	Args:
		body: Частичное обновление настроек алерта (цвета, шрифт, длительность, TTS, изображение).

	Returns:
		AlertSettingsResponse: Полные актуальные настройки после обновления.

	Raises:
		401: Пользователь не аутентифицирован.
		403: Доступно только стримерам.
		422: Неверный формат цвета или значение вне допустимого диапазона.
	"""
	log = logger.bind(request_user_id=user.telegram_id)
	log.debug("PATCH /settings/alert")
	result = await settings_service.update_alert(
		user,
		bg_color=body.bg_color,
		text_color=body.text_color,
		font=body.font,
		duration_sec=body.duration_sec,
		image_enabled=body.image_enabled,
		tts_enabled=body.tts_enabled,
		tts_voice=body.tts_voice,
	)
	log.info("alert settings updated")
	return settings_schema.AlertSettingsResponse(
		bg_color=result.bg_color,
		text_color=result.text_color,
		font=result.font,
		duration_sec=result.duration_sec,
		image_enabled=result.image_enabled,
		tts_enabled=result.tts_enabled,
		tts_voice=result.tts_voice,
	)


@router.post(
	"/alert/test",
	response_model=settings_schema.AlertTestResponse,
	status_code=status.HTTP_200_OK,
	summary="Отправить тестовый алерт в виджет",
)
@inject
async def test_alert(
	user: CurrentUserDep,
	settings_service: FromDishka[SettingsService],
) -> settings_schema.AlertTestResponse:
	"""Отправляет тестовый алерт в OBS-виджет с текущими настройками стиля.

	Используется для предпросмотра внешнего вида алерта без реального доната.
	Требует активного стрима — виджет должен быть подключён к WebSocket.

	Returns:
		AlertTestResponse: Подтверждение отправки.

	Raises:
		401: Пользователь не аутентифицирован.
		403: Доступно только стримерам.
		404: Нет активного стрима (виджет не подключён).
	"""
	log = logger.bind(request_user_id=user.telegram_id)
	log.debug("POST /settings/alert/test")
	await settings_service.test_alert(user)
	log.info("test alert sent")
	return settings_schema.AlertTestResponse(
		status="sent",
		message="Тестовый алерт отправлен в виджет",
	)


# ── Goal ──────────────────────────────────────────────────────────────────────

@router.get("/goal", response_model=settings_schema.GoalResponse, summary="Цель сбора стримера")
@inject
async def get_goal(
	user: CurrentUserDep,
	settings_service: FromDishka[SettingsService],
) -> settings_schema.GoalResponse:
	"""Возвращает текущую цель сбора стримера.

	Если цель ещё не задана — автоматически создаётся со значениями по умолчанию.
	`current_amount` обновляется автоматически при каждом донате.

	Returns:
		GoalResponse: Название, целевая и текущая суммы.

	Raises:
		401: Пользователь не аутентифицирован.
		403: Доступно только стримерам.
	"""
	log = logger.bind(request_user_id=user.telegram_id)
	log.debug("GET /settings/goal")
	result = await settings_service.get_goal(user)
	return settings_schema.GoalResponse(
		title=result.title,
		target_amount=result.target_amount,
		current_amount=result.current_amount,
	)


@router.patch("/goal", response_model=settings_schema.GoalResponse, summary="Обновить цель сбора")
@inject
async def update_goal(
	body: settings_schema.GoalBody,
	user: CurrentUserDep,
	settings_service: FromDishka[SettingsService],
) -> settings_schema.GoalResponse:
	"""Обновляет название и/или целевую сумму цели сбора. Все поля опциональны.

	Args:
		body: Новое название (до 128 символов) и/или целевая сумма (1–1 000 000 монет).

	Returns:
		GoalResponse: Актуальная цель после обновления.

	Raises:
		401: Пользователь не аутентифицирован.
		403: Доступно только стримерам.
		422: Пустое название или целевая сумма вне допустимого диапазона.
	"""
	log = logger.bind(request_user_id=user.telegram_id)
	log.debug("PATCH /settings/goal")
	result = await settings_service.update_goal(
		user,
		title=body.title,
		target_amount=body.target_amount,
	)
	log.info("goal updated")
	return settings_schema.GoalResponse(
		title=result.title,
		target_amount=result.target_amount,
		current_amount=result.current_amount,
	)


# ── Stop Words ────────────────────────────────────────────────────────────────

@router.get("/stopwords", response_model=list[settings_schema.StopWordResponse], summary="Список стоп-слов стримера")
@inject
async def get_stopwords(
	user: CurrentUserDep,
	settings_service: FromDishka[SettingsService],
) -> list[settings_schema.StopWordResponse]:
	"""Возвращает все стоп-слова стримера.

	Сообщения донатов, содержащие стоп-слово, отклоняются на этапе модерации.
	Слова хранятся в нижнем регистре.

	Returns:
		list[StopWordResponse]: Список стоп-слов с их ID.

	Raises:
		401: Пользователь не аутентифицирован.
		403: Доступно только стримерам.
	"""
	log = logger.bind(request_user_id=user.telegram_id)
	log.debug("GET /settings/stopwords")
	words = await settings_service.get_stopwords(user)
	return [settings_schema.StopWordResponse(id=w.id, word=w.word) for w in words]


@router.post(
	"/stopwords",
	response_model=settings_schema.StopWordResponse,
	status_code=status.HTTP_201_CREATED,
	summary="Добавить стоп-слово",
)
@inject
async def add_stopword(
	body: settings_schema.StopWordBody,
	user: CurrentUserDep,
	settings_service: FromDishka[SettingsService],
) -> settings_schema.StopWordResponse:
	"""Добавляет новое стоп-слово. Слово приводится к нижнему регистру автоматически.

	Args:
		body: Слово для блокировки (до 64 символов, регистр не важен).

	Returns:
		StopWordResponse: Созданное стоп-слово с присвоенным ID.

	Raises:
		401: Пользователь не аутентифицирован.
		403: Доступно только стримерам.
		409: Такое стоп-слово уже существует.
		422: Пустая строка.
	"""
	log = logger.bind(request_user_id=user.telegram_id)
	log.debug("POST /settings/stopwords")
	word = await settings_service.add_stopword(user, body.word)
	log.info("stopword added", word_id=word.id)
	return settings_schema.StopWordResponse(id=word.id, word=word.word)


@router.delete("/stopwords/{word_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Удалить стоп-слово")
@inject
async def delete_stopword(
	word_id: int,
	user: CurrentUserDep,
	settings_service: FromDishka[SettingsService],
) -> None:
	"""Удаляет стоп-слово по ID. Ответ — 204 No Content.

	Args:
		word_id: ID стоп-слова из `GET /settings/stopwords`.

	Raises:
		401: Пользователь не аутентифицирован.
		403: Стоп-слово принадлежит другому стримеру.
		404: Стоп-слово с таким ID не найдено.
	"""
	log = logger.bind(request_user_id=user.telegram_id, word_id=word_id)
	log.debug("DELETE /settings/stopwords/{word_id}")
	await settings_service.delete_stopword(user, word_id)
	log.info("stopword deleted")


# ── Passive Income ────────────────────────────────────────────────────────────

@router.get("/passive-income", response_model=settings_schema.PassiveIncomeResponse, summary="Настройки пассивного дохода")
@inject
async def get_passive_income(
	user: CurrentUserDep,
	settings_service: FromDishka[SettingsService],
) -> settings_schema.PassiveIncomeResponse:
	"""Возвращает настройки пассивного дохода стримера.

	Пассивный доход — автоматическое начисление монет зрителям, подключённым
	к стриму через Mini App. Управляется cron-тасом воркера.

	Returns:
		PassiveIncomeResponse: Статус включения, монеты за интервал и интервал в минутах.

	Raises:
		401: Пользователь не аутентифицирован.
		403: Доступно только стримерам.
	"""
	log = logger.bind(request_user_id=user.telegram_id)
	log.debug("GET /settings/passive-income")
	result = await settings_service.get_passive_income(user)
	return settings_schema.PassiveIncomeResponse(
		enabled=result.enabled,
		coins_per_interval=result.coins_per_interval,
		interval_minutes=result.interval_minutes,
	)


@router.patch("/passive-income", response_model=settings_schema.PassiveIncomeResponse, summary="Обновить настройки пассивного дохода")
@inject
async def update_passive_income(
	body: settings_schema.PassiveIncomeBody,
	user: CurrentUserDep,
	settings_service: FromDishka[SettingsService],
) -> settings_schema.PassiveIncomeResponse:
	"""Обновляет настройки пассивного дохода. Все поля опциональны.

	Изменения вступают в силу на следующем тике cron-таски (каждую минуту).

	Args:
		body: Флаг включения, монеты за интервал (1–1000) и интервал в минутах (1–60).

	Returns:
		PassiveIncomeResponse: Актуальные настройки после обновления.

	Raises:
		401: Пользователь не аутентифицирован.
		403: Доступно только стримерам.
		422: Значения монет или интервала вне допустимого диапазона.
	"""
	log = logger.bind(request_user_id=user.telegram_id)
	log.debug("PATCH /settings/passive-income")
	result = await settings_service.update_passive_income(
		user,
		enabled=body.enabled,
		coins_per_interval=body.coins_per_interval,
		interval_minutes=body.interval_minutes,
	)
	log.info("passive income settings updated")
	return settings_schema.PassiveIncomeResponse(
		enabled=result.enabled,
		coins_per_interval=result.coins_per_interval,
		interval_minutes=result.interval_minutes,
	)
