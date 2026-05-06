"""Сервис настроек стримера: alert style, goal, stop-words, passive income, test alert."""

from __future__ import annotations

from redis.asyncio import Redis
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exc.exceptions import (
	ConflictError,
	ForbiddenError,
	NotFoundError,
	StreamerRequiredError,
	StreamNotActiveError,
)
from src.repos import sql
from src.repos.redis import ws_queue_repo
from src.schemas.dataclasses.settings import (
	AlertSettingsCreateDTO,
	AlertSettingsDTO,
	PassiveIncomeSettingsCreateDTO,
	PassiveIncomeSettingsDTO,
	StopWordCreateDTO,
	StopWordDTO,
	StreamGoalCreateDTO,
	StreamGoalDTO,
)
from src.schemas.dataclasses.users import UserDTO
from src.schemas.enums.users import UserRole
from src.services.logger import get_logger

logger = get_logger().bind(layer="service", module="settings")

_DEFAULT_ALERT = AlertSettingsCreateDTO
_DEFAULT_GOAL = StreamGoalCreateDTO
_DEFAULT_PASSIVE = PassiveIncomeSettingsCreateDTO


class SettingsService:
	def __init__(self, session: AsyncSession, redis: Redis) -> None:
		self._session = session
		self._redis = redis

	# ── Alert Style ──────────────────────────────────────────────────────────

	async def get_alert(self, user: UserDTO) -> AlertSettingsDTO:
		log = logger.bind(request_user_id=user.telegram_id)
		log.debug("settings.get_alert")
		self._require_streamer(user)

		settings = await sql.alert_settings_repo.get_by_streamer_id(
			self._session,
			user.telegram_id,
		)
		if settings is None:
			settings = await sql.alert_settings_repo.create(
				self._session,
				AlertSettingsCreateDTO(streamer_id=user.telegram_id),
			)
			log.info("alert settings created with defaults")
		return settings

	async def update_alert(
		self,
		user: UserDTO,
		**fields: object,
	) -> AlertSettingsDTO:
		log = logger.bind(request_user_id=user.telegram_id)
		log.info("settings.update_alert started")
		self._require_streamer(user)

		settings = await sql.alert_settings_repo.get_by_streamer_id(
			self._session,
			user.telegram_id,
		)
		if settings is None:
			settings = await sql.alert_settings_repo.create(
				self._session,
				AlertSettingsCreateDTO(streamer_id=user.telegram_id),
			)

		updated = await sql.alert_settings_repo.update(
			self._session,
			user.telegram_id,
			**fields,
		)
		if updated is None:
			raise NotFoundError()

		log.info("settings.update_alert done")
		return updated

	async def test_alert(self, user: UserDTO) -> None:
		log = logger.bind(request_user_id=user.telegram_id)
		log.info("settings.test_alert started")
		self._require_streamer(user)

		active = await sql.stream_sessions_repo.get_active_by_streamer_id(
			self._session,
			user.telegram_id,
		)
		if active is None:
			log.error("test_alert: no active stream")
			raise StreamNotActiveError()

		settings = await sql.alert_settings_repo.get_by_streamer_id(
			self._session,
			user.telegram_id,
		)

		event = {
			"type": "test_alert",
			"donor_name": "Тест",
			"amount": 100,
			"message": "Это тестовый донат!",
			"audio_url": None,
			"image_url": None,
			"style": {
				"bg_color": settings.bg_color if settings else "#1a1a2e",
				"text_color": settings.text_color if settings else "#ffffff",
				"font": settings.font if settings else "Roboto",
				"duration_sec": settings.duration_sec if settings else 5,
			},
		}
		await ws_queue_repo.push_control(
			self._redis,
			active.stream_token,
			event,
		)
		log.info("test_alert pushed", stream_token=active.stream_token)

	# ── Goal ─────────────────────────────────────────────────────────────────

	async def get_goal(self, user: UserDTO) -> StreamGoalDTO:
		log = logger.bind(request_user_id=user.telegram_id)
		log.debug("settings.get_goal")
		self._require_streamer(user)

		goal = await sql.stream_goals_repo.get_by_streamer_id(
			self._session,
			user.telegram_id,
		)
		if goal is None:
			goal = await sql.stream_goals_repo.create(
				self._session,
				StreamGoalCreateDTO(streamer_id=user.telegram_id),
			)
			log.info("goal created with defaults")
		return goal

	async def update_goal(
		self,
		user: UserDTO,
		**fields: object,
	) -> StreamGoalDTO:
		log = logger.bind(request_user_id=user.telegram_id)
		log.info("settings.update_goal started")
		self._require_streamer(user)

		goal = await sql.stream_goals_repo.get_by_streamer_id(
			self._session,
			user.telegram_id,
		)
		if goal is None:
			goal = await sql.stream_goals_repo.create(
				self._session,
				StreamGoalCreateDTO(streamer_id=user.telegram_id),
			)

		updated = await sql.stream_goals_repo.update(
			self._session,
			user.telegram_id,
			**fields,
		)
		if updated is None:
			raise NotFoundError()

		log.info("settings.update_goal done")
		return updated

	# ── Stop Words ────────────────────────────────────────────────────────────

	async def get_stopwords(self, user: UserDTO) -> list[StopWordDTO]:
		log = logger.bind(request_user_id=user.telegram_id)
		log.debug("settings.get_stopwords")
		self._require_streamer(user)
		return await sql.stop_words_repo.get_by_streamer_id(
			self._session,
			user.telegram_id,
		)

	async def add_stopword(self, user: UserDTO, word: str) -> StopWordDTO:
		log = logger.bind(request_user_id=user.telegram_id, request_word=word)
		log.info("settings.add_stopword started")
		self._require_streamer(user)

		word = word.strip().lower()
		if not word:
			raise ConflictError()

		try:
			result = await sql.stop_words_repo.create(
				self._session,
				StopWordCreateDTO(streamer_id=user.telegram_id, word=word),
			)
		except IntegrityError:
			raise ConflictError()

		log.info("settings.add_stopword done", word_id=result.id)
		return result

	async def delete_stopword(self, user: UserDTO, word_id: int) -> None:
		log = logger.bind(request_user_id=user.telegram_id, word_id=word_id)
		log.info("settings.delete_stopword started")
		self._require_streamer(user)

		word = await sql.stop_words_repo.get_by_id(self._session, word_id)
		if word is None:
			raise NotFoundError()
		if word.streamer_id != user.telegram_id:
			raise ForbiddenError()

		await sql.stop_words_repo.delete(self._session, word_id)
		log.info("settings.delete_stopword done")

	# ── Passive Income ────────────────────────────────────────────────────────

	async def get_passive_income(
		self,
		user: UserDTO,
	) -> PassiveIncomeSettingsDTO:
		log = logger.bind(request_user_id=user.telegram_id)
		log.debug("settings.get_passive_income")
		self._require_streamer(user)

		settings = await sql.passive_income_settings_repo.get_by_streamer_id(
			self._session,
			user.telegram_id,
		)
		if settings is None:
			settings = await sql.passive_income_settings_repo.create(
				self._session,
				PassiveIncomeSettingsCreateDTO(streamer_id=user.telegram_id),
			)
			log.info("passive income settings created with defaults")
		return settings

	async def update_passive_income(
		self,
		user: UserDTO,
		**fields: object,
	) -> PassiveIncomeSettingsDTO:
		log = logger.bind(request_user_id=user.telegram_id)
		log.info("settings.update_passive_income started")
		self._require_streamer(user)

		settings = await sql.passive_income_settings_repo.get_by_streamer_id(
			self._session,
			user.telegram_id,
		)
		if settings is None:
			settings = await sql.passive_income_settings_repo.create(
				self._session,
				PassiveIncomeSettingsCreateDTO(streamer_id=user.telegram_id),
			)

		updated = await sql.passive_income_settings_repo.update(
			self._session,
			user.telegram_id,
			**fields,
		)
		if updated is None:
			raise NotFoundError()

		log.info("settings.update_passive_income done")
		return updated

	# ── Internal ─────────────────────────────────────────────────────────────

	@staticmethod
	def _require_streamer(user: UserDTO) -> None:
		if user.role != UserRole.STREAMER:
			raise StreamerRequiredError()
