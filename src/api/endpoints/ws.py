"""WebSocket endpoint для OBS-виджета.

Протокол:
  Client → Server: ping | ready | alert_displayed
  Server → Client: pong | connected | new_alert | goal_updated | stream_stopped | test_alert

Архитектура:
  1. arq worker обрабатывает TTS+Image, возвращает результат (dict с raw S3 ключами).
  2. DonationService после enqueue_job кладёт job_id в ws:jobs:{token} (LPUSH).
  3. Этот WS handler блокируется на BLPOP ws:jobs:{token} | ws:control:{token}.
  4. Получив job_id — читает результат через ArqJob.result(), генерирует presigned URLs,
     отправляет new_alert + goal_updated в WebSocket.
  5. Получив control event (stream_stopped, test_alert) — форвардит в WebSocket.
"""

from __future__ import annotations

import asyncio
import contextlib
import json

from arq.connections import ArqRedis
from arq.jobs import Job as ArqJob
from dishka.integrations.fastapi import DishkaRoute, FromDishka, inject
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.core.storages import S3Manager
from src.repos import sql
from src.repos.redis import ws_queue_repo
from src.repos.s3 import media_repo
from src.schemas.dataclasses.donations import DonationMediaResultDTO
from src.services.logger import AbstractLogger, get_logger

router = APIRouter(route_class=DishkaRoute)

logger = get_logger().bind(layer="endpoint", module="ws")


@router.websocket("/ws/{stream_token}")
@inject
async def ws_obs_widget(
	websocket: WebSocket,
	stream_token: str,
	session_factory: FromDishka[async_sessionmaker[AsyncSession]],
	arq_pool: FromDishka[ArqRedis],
	s3_manager: FromDishka[S3Manager],
) -> None:
	log = logger.bind(stream_token=stream_token)
	log.debug("ws connection attempt")

	# ── Валидация токена ─────────────────────────────────────────────────────
	async with session_factory() as session:
		async with session.begin():
			stream_session = (
				await sql.stream_sessions_repo.get_by_stream_token(
					session,
					stream_token,
				)
			)
			if stream_session is None or not stream_session.is_active:
				log.error("ws invalid or inactive stream token")
				await websocket.close(code=4004)
				return
			streamer = await sql.users_repo.get_by_telegram_id(
				session,
				stream_session.streamer_id,
			)
			streamer_name = (
				streamer.display_name or streamer.username or "Стример"
				if streamer
				else "Стример"
			)
			session_id = stream_session.id
			streamer_id = stream_session.streamer_id

	await websocket.accept()
	log.info("ws accepted", session_id=session_id)

	# ── Ждём ready, отвечаем connected ───────────────────────────────────────
	try:
		first = await asyncio.wait_for(websocket.receive_json(), timeout=10.0)
		if isinstance(first, dict) and first.get("type") == "ready":
			await websocket.send_json(
				{
					"type": "connected",
					"streamer": streamer_name,
					"session_id": session_id,
				},
			)
			log.debug("ws connected sent")
	except (TimeoutError, Exception):
		await websocket.send_json(
			{
				"type": "connected",
				"streamer": streamer_name,
				"session_id": session_id,
			},
		)

	# ── Два параллельных цикла ────────────────────────────────────────────────
	t_client = asyncio.create_task(_client_loop(websocket, log))
	t_queue = asyncio.create_task(
		_queue_loop(
			websocket,
			arq_pool,
			s3_manager,
			session_factory,
			stream_token,
			streamer_id,
			log,
		),
	)

	try:
		done, pending = await asyncio.wait(
			[t_client, t_queue],
			return_when=asyncio.FIRST_COMPLETED,
		)
		for task in pending:
			task.cancel()
			with contextlib.suppress(asyncio.CancelledError, Exception):
				await task
	finally:
		await ws_queue_repo.cleanup(arq_pool, stream_token)
		log.info("ws disconnected", session_id=session_id)


async def _client_loop(websocket: WebSocket, log: AbstractLogger) -> None:
	"""Обрабатываем сообщения от OBS-виджета."""
	while True:
		try:
			data = await websocket.receive_json()
		except (WebSocketDisconnect, Exception):
			return

		msg_type = data.get("type") if isinstance(data, dict) else None
		if msg_type == "ping":
			await websocket.send_json({"type": "pong"})
		elif msg_type == "alert_displayed":
			log.debug("alert_displayed", donation_id=data.get("donation_id"))


async def _queue_loop(
	websocket: WebSocket,
	arq_pool: ArqRedis,
	s3_manager: S3Manager,
	session_factory: async_sessionmaker[AsyncSession],
	stream_token: str,
	streamer_id: int,
	log: AbstractLogger,
) -> None:
	"""Читаем события из Redis-очередей: arq job results + control events."""
	while True:
		queue_type, value = await ws_queue_repo.pop_next(
			arq_pool,
			stream_token,
			timeout=30,
		)

		if queue_type is None or value is None:
			# timeout — продолжаем ждать
			continue

		if queue_type == "control":
			try:
				event = json.loads(value)
				await websocket.send_json(event)
				if event.get("type") == "stream_stopped":
					log.info("stream_stopped sent, closing ws")
					await websocket.close()
					return
			except Exception as e:
				log.error("control event handling failed", error=str(e))
			continue

		# queue_type == "job": читаем результат arq-таски
		job_id = value
		try:
			job = ArqJob(job_id, arq_pool)
			result: DonationMediaResultDTO = await job.result(
				timeout=120.0,
				poll_delay=0.5,
			)
		except Exception as e:
			log.error("arq job result failed", job_id=job_id, error=str(e))
			continue

		# ── Presigned URLs ────────────────────────────────────────────────────
		audio_url, image_url = await asyncio.gather(
			media_repo.resolve_presigned_url(s3_manager, result.audio_key),
			media_repo.resolve_presigned_url(s3_manager, result.image_key),
			return_exceptions=True,
		)
		if isinstance(audio_url, BaseException):
			log.error("audio presign failed", error=str(audio_url))
			audio_url = None
		if isinstance(image_url, BaseException):
			log.error("image presign failed", error=str(image_url))
			image_url = None

		# ── new_alert ─────────────────────────────────────────────────────────
		try:
			await websocket.send_json(
				{
					"type": "new_alert",
					"donation_id": result.donation_id,
					"donor_name": result.donor_name,
					"amount": result.amount,
					"message": result.message,
					"audio_url": audio_url,
					"image_url": image_url,
					"style": {
						"bg_color": result.alert_bg_color,
						"text_color": result.alert_text_color,
						"font": result.alert_font,
						"duration_sec": result.alert_duration_sec,
					},
				},
			)
			log.info("new_alert sent", donation_id=result.donation_id)
		except Exception as e:
			log.error("ws send new_alert failed", error=str(e))
			return

		# ── goal_updated ──────────────────────────────────────────────────────
		try:
			async with session_factory() as session:
				async with session.begin():
					goal = await sql.stream_goals_repo.get_by_streamer_id(
						session,
						streamer_id,
					)

			if goal and goal.target_amount > 0:
				percent = round(goal.current_amount / goal.target_amount * 100)
				await websocket.send_json(
					{
						"type": "goal_updated",
						"title": goal.title,
						"target_amount": goal.target_amount,
						"current_amount": goal.current_amount,
						"percent": percent,
					},
				)
				log.info("goal_updated sent")
		except Exception as e:
			log.error("goal_updated failed", error=str(e))
