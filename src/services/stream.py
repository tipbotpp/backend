from __future__ import annotations

import secrets

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.configs import cfg
from src.core.exc.exceptions import (
	StreamAlreadyActiveError,
	StreamerRequiredError,
	StreamNotActiveError,
)
from src.repos import sql
from src.schemas.dataclasses.donations import SessionStatsDTO
from src.schemas.dataclasses.streams import (
	StreamSessionCreateDTO,
	StreamSessionDTO,
)
from src.schemas.dataclasses.users import UserDTO
from src.schemas.enums.users import UserRole
from src.services.logger import get_logger
from src.utils import local_time

logger = get_logger().bind(layer="service", module="stream")


def _widget_url(stream_token: str) -> str:
	return f"{cfg.app.widget_base_url}/{stream_token}"


def _ws_url(stream_token: str) -> str:
	base = cfg.app.public_url.replace("https://", "wss://").replace("http://", "ws://")
	return f"{base}/ws/{stream_token}"


class StreamService:
	def __init__(self, session: AsyncSession) -> None:
		self._session = session

	async def start(
		self,
		user: UserDTO,
		passive_income_enabled: bool,
	) -> StreamSessionDTO:
		log = logger.bind(request_user_id=user.telegram_id)
		log.info("stream.start started")

		if user.role != UserRole.STREAMER:
			log.error("streamer role required", user_role=user.role)
			raise StreamerRequiredError()

		existing = await sql.stream_sessions_repo.get_active_by_streamer_id(
			self._session, user.telegram_id,
		)
		if existing is not None:
			log.error("stream already active", session_id=existing.id)
			raise StreamAlreadyActiveError()

		stream_token = secrets.token_urlsafe(32)
		session = await sql.stream_sessions_repo.create(
			self._session,
			StreamSessionCreateDTO(
				streamer_id=user.telegram_id,
				stream_token=stream_token,
				is_active=True,
				passive_income_enabled=passive_income_enabled,
			),
		)
		log.info("stream.start done", session_id=session.id, stream_token=stream_token)
		return session

	async def stop(self, user: UserDTO) -> tuple[StreamSessionDTO, SessionStatsDTO]:
		log = logger.bind(request_user_id=user.telegram_id)
		log.info("stream.stop started")

		if user.role != UserRole.STREAMER:
			log.error("streamer role required", user_role=user.role)
			raise StreamerRequiredError()

		active = await sql.stream_sessions_repo.get_active_by_streamer_id(
			self._session, user.telegram_id,
		)
		if active is None:
			log.error("no active stream session")
			raise StreamNotActiveError()

		ended_at = local_time.now()
		stopped = await sql.stream_sessions_repo.deactivate(self._session, active.id, ended_at)
		if stopped is None:
			raise StreamNotActiveError()
		stats = await sql.donations_repo.get_session_stats(self._session, active.id)

		log.info("stream.stop done", session_id=active.id)
		return stopped, stats

	async def get_status(self, user: UserDTO) -> StreamSessionDTO | None:
		log = logger.bind(request_user_id=user.telegram_id)
		log.debug("stream.get_status started")
		active = await sql.stream_sessions_repo.get_active_by_streamer_id(
			self._session, user.telegram_id,
		)
		log.debug("stream.get_status done", is_live=active is not None)
		return active


def make_widget_url(stream_token: str) -> str:
	return _widget_url(stream_token)


def make_ws_url(stream_token: str) -> str:
	return _ws_url(stream_token)
