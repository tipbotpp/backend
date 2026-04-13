"""WebSocket endpoint для OBS-виджета.

Протокол:
  Client → Server: ping | ready | alert_displayed
  Server → Client: pong | connected | new_alert | goal_updated | stream_stopped | test_alert
"""
from __future__ import annotations

import asyncio
import json

from dishka.integrations.fastapi import DishkaRoute, FromDishka, inject
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.repos import sql
from src.services.logger import get_logger

router = APIRouter(route_class=DishkaRoute)

logger = get_logger().bind(layer="endpoint", module="ws")

_CHANNEL_PREFIX = "ws:"


@router.websocket("/ws/{stream_token}")
@inject
async def ws_obs_widget(
	websocket: WebSocket,
	stream_token: str,
	session_factory: FromDishka[async_sessionmaker[AsyncSession]],
	redis: FromDishka[Redis],
) -> None:
	log = logger.bind(stream_token=stream_token)
	log.debug("ws connection attempt")

	# ── Валидация токена (короткоживущая сессия) ──────────────────────────────
	async with session_factory() as session:
		async with session.begin():
			stream_session = await sql.stream_sessions_repo.get_by_stream_token(session, stream_token)
			if stream_session is None or not stream_session.is_active:
				log.error("ws invalid or inactive stream token")
				await websocket.close(code=4004)
				return
			streamer = await sql.users_repo.get_by_telegram_id(session, stream_session.streamer_id)
			streamer_name = (
				streamer.display_name or streamer.username or "Стример"
				if streamer else "Стример"
			)
			session_id = stream_session.id

	await websocket.accept()
	log.info("ws accepted", session_id=session_id)

	# ── Ждём ready, отвечаем connected ───────────────────────────────────────
	try:
		first = await asyncio.wait_for(websocket.receive_json(), timeout=10.0)
		if isinstance(first, dict) and first.get("type") == "ready":
			await websocket.send_json({
				"type": "connected",
				"streamer": streamer_name,
				"session_id": session_id,
			})
			log.debug("ws connected sent")
	except (asyncio.TimeoutError, Exception):
		# Клиент не прислал ready — всё равно работаем
		await websocket.send_json({
			"type": "connected",
			"streamer": streamer_name,
			"session_id": session_id,
		})

	# ── Pub/Sub подписка ──────────────────────────────────────────────────────
	channel = f"{_CHANNEL_PREFIX}{stream_token}"
	pubsub = redis.pubsub()
	await pubsub.subscribe(channel)
	log.debug("ws subscribed to redis", channel=channel)

	# ── Два параллельных цикла ────────────────────────────────────────────────
	t_client = asyncio.create_task(_client_loop(websocket, log))
	t_redis = asyncio.create_task(_redis_loop(websocket, pubsub, log))

	try:
		done, pending = await asyncio.wait(
			[t_client, t_redis],
			return_when=asyncio.FIRST_COMPLETED,
		)
		for task in pending:
			task.cancel()
			try:
				await task
			except (asyncio.CancelledError, Exception):
				pass
	finally:
		await pubsub.unsubscribe(channel)
		await pubsub.aclose()
		log.info("ws disconnected", session_id=session_id)


async def _client_loop(websocket: WebSocket, log) -> None:
	"""Обрабатываем сообщения от OBS-виджета."""
	while True:
		try:
			data = await websocket.receive_json()
		except WebSocketDisconnect:
			return
		except Exception:
			return

		msg_type = data.get("type") if isinstance(data, dict) else None
		if msg_type == "ping":
			await websocket.send_json({"type": "pong"})
		elif msg_type == "alert_displayed":
			log.debug("alert_displayed", donation_id=data.get("donation_id"))


async def _redis_loop(websocket: WebSocket, pubsub, log) -> None:
	"""Пересылаем события из Redis pub/sub в WebSocket."""
	async for message in pubsub.listen():
		if message["type"] != "message":
			continue

		raw = message["data"]
		text = raw.decode() if isinstance(raw, bytes) else raw
		try:
			await websocket.send_text(text)
		except Exception:
			return

		# Если стрим остановлен — закрываем соединение со стороны сервера
		try:
			parsed = json.loads(text)
			if parsed.get("type") == "stream_stopped":
				log.info("stream_stopped received, closing ws")
				await websocket.close()
				return
		except Exception:
			pass
