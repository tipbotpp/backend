from __future__ import annotations

from dishka.integrations.fastapi import DishkaRoute, FromDishka, inject
from fastapi import APIRouter
from redis.asyncio import Redis

from src.di.deps.auth import CurrentUserDep
from src.repos.redis import ws_queue_repo
from src.schemas.pydantic import stream as stream_schema
from src.services.logger import get_logger
from src.services.stream import StreamService, make_widget_url, make_ws_url
from src.utils import local_time

router = APIRouter(prefix="/stream", route_class=DishkaRoute)

logger = get_logger().bind(layer="endpoint", module="stream")


@router.post("/start", response_model=stream_schema.StreamStartResponse, summary="Начать стрим")
@inject
async def start_stream(
	body: stream_schema.StreamStartBody,
	stream_service: FromDishka[StreamService],
	request_user: CurrentUserDep,
) -> stream_schema.StreamStartResponse:
	"""Запускает новую сессию стрима для стримера.

	Генерирует уникальный `stream_token`, который используется для подключения
	OBS Browser Source к виджету и WebSocket. Токен действителен до остановки стрима.

	Args:
		body: Флаг включения пассивного дохода для зрителей.
		request_user: Текущий аутентифицированный пользователь (DI).
		stream_service: Сервис стрима (DI).

	Returns:
		StreamStartResponse: Токен сессии, URL виджета и WebSocket.

	Raises:
		401: Пользователь не аутентифицирован.
		403: Доступно только стримерам.
		409: Стрим уже запущен.
	"""
	log = logger.bind(request_user_id=request_user.telegram_id)
	log.debug("POST /stream/start")

	stream_session = await stream_service.start(request_user, body.passive_income_enabled)

	log.info("stream started", session_id=stream_session.id)
	return stream_schema.StreamStartResponse(
		session_id=stream_session.id,
		stream_token=stream_session.stream_token,
		widget_url=make_widget_url(stream_session.stream_token),
		ws_url=make_ws_url(stream_session.stream_token),
		started_at=stream_session.started_at,
	)


@router.post("/stop", response_model=stream_schema.StreamStopResponse, summary="Завершить стрим")
@inject
async def stop_stream(
	stream_service: FromDishka[StreamService],
	redis: FromDishka[Redis],
	request_user: CurrentUserDep,
) -> stream_schema.StreamStopResponse:
	"""Завершает текущую активную сессию стрима.

	Отправляет событие `stream_stopped` в OBS-виджет через WebSocket,
	после чего виджет должен отключиться. Возвращает итоговую статистику сессии.

	Args:
		request_user: Текущий аутентифицированный пользователь (DI).
		stream_service: Сервис стрима (DI).
		redis: Redis-клиент для отправки события в WS-очередь (DI).

	Returns:
		StreamStopResponse: Общая сумма донатов, их количество и длительность стрима.

	Raises:
		401: Пользователь не аутентифицирован.
		403: Доступно только стримерам.
		404: Нет активного стрима для остановки.
	"""
	log = logger.bind(request_user_id=request_user.telegram_id)
	log.debug("POST /stream/stop")

	stopped, stats = await stream_service.stop(request_user)

	await ws_queue_repo.push_control(
		redis,
		stopped.stream_token,
		{"type": "stream_stopped", "session_id": stopped.id},
	)
	log.info("stream_stopped pushed to ws queue", stream_token=stopped.stream_token)

	ended_at = stopped.ended_at or local_time.now()
	duration_seconds = int((ended_at - stopped.started_at).total_seconds())

	log.info("stream stopped", session_id=stopped.id, duration_seconds=duration_seconds)
	return stream_schema.StreamStopResponse(
		session_id=stopped.id,
		total_collected=stats.total_collected,
		donations_count=stats.donations_count,
		duration_seconds=duration_seconds,
		ended_at=ended_at,
	)


@router.get("/status", response_model=stream_schema.StreamStatusResponse, summary="Статус текущего стрима")
@inject
async def stream_status(
	stream_service: FromDishka[StreamService],
	request_user: CurrentUserDep,
) -> stream_schema.StreamStatusResponse:
	"""Возвращает статус текущего стрима стримера.

	Если стрим не запущен — `is_live: false`, остальные поля `null`.

	Args:
		request_user: Текущий аутентифицированный пользователь (DI).
		stream_service: Сервис стрима (DI).

	Returns:
		StreamStatusResponse: Статус стрима, ID сессии и URL виджета.

	Raises:
		401: Пользователь не аутентифицирован.
		403: Доступно только стримерам.
	"""
	log = logger.bind(request_user_id=request_user.telegram_id)
	log.debug("GET /stream/status")

	active = await stream_service.get_status(request_user)

	if active is None:
		return stream_schema.StreamStatusResponse(
			is_live=False,
			session_id=None,
			started_at=None,
			widget_url=None,
		)

	return stream_schema.StreamStatusResponse(
		is_live=True,
		session_id=active.id,
		started_at=active.started_at,
		widget_url=make_widget_url(active.stream_token),
	)
