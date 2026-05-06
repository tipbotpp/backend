from __future__ import annotations

from dishka.integrations.fastapi import DishkaRoute, FromDishka, inject
from fastapi import APIRouter
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exc.exceptions import NotFoundError
from src.repos import sql
from src.schemas.dataclasses.settings import AlertSettingsDTO
from src.schemas.pydantic.widget import (
	WidgetAlertStyleSchema,
	WidgetResponse,
	WidgetStreamerSchema,
)
from src.services.logger import get_logger
from src.services.stream import make_ws_url

router = APIRouter(prefix="/widget", route_class=DishkaRoute)

logger = get_logger().bind(layer="endpoint", module="widget")

_DEFAULT_ALERT_STYLE = AlertSettingsDTO(
	id=0,
	streamer_id=0,
	bg_color="#1a1a2e",
	text_color="#ffffff",
	font="Roboto",
	duration_sec=5,
	image_enabled=True,
	tts_enabled=True,
	tts_voice="silero_v3_ru",
)


@router.get(
	"/{stream_token}",
	response_model=WidgetResponse,
	summary="Данные виджета для OBS Browser Source",
)
@inject
async def get_widget(
	stream_token: str,
	session: FromDishka[AsyncSession],
) -> WidgetResponse:
	"""Возвращает конфигурацию виджета для OBS Browser Source. Эндпоинт публичный.

	Используется фронтендом виджета при инициализации для получения
	настроек алерта и WebSocket URL. Токен стрима является секретом —
	его знает только стример и его браузерный источник.

	Args:
		stream_token: Уникальный токен активного стрима из `POST /stream/start`.

	Returns:
		WidgetResponse: Данные стримера, стиль алерта и WebSocket URL.

	Raises:
		404: Стрим не найден или уже завершён.
	"""
	log = logger.bind(stream_token=stream_token)
	log.debug("GET /widget/{stream_token}")

	stream_session = await sql.stream_sessions_repo.get_by_stream_token(
		session,
		stream_token,
	)
	if stream_session is None or not stream_session.is_active:
		log.error("widget: stream not found or inactive")
		raise NotFoundError()

	streamer = await sql.users_repo.get_by_telegram_id(
		session,
		stream_session.streamer_id,
	)
	if streamer is None:
		log.error("widget: streamer not found")
		raise NotFoundError()

	alert = await sql.alert_settings_repo.get_by_streamer_id(
		session,
		stream_session.streamer_id,
	)
	style = alert or _DEFAULT_ALERT_STYLE

	log.info("widget served", session_id=stream_session.id)
	return WidgetResponse(
		stream_token=stream_token,
		streamer=WidgetStreamerSchema(
			username=streamer.username,
			display_name=streamer.display_name,
		),
		alert_style=WidgetAlertStyleSchema(
			bg_color=style.bg_color,
			text_color=style.text_color,
			font=style.font,
			duration_sec=style.duration_sec,
		),
		ws_url=make_ws_url(stream_token),
	)
