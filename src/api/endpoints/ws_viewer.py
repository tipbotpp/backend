"""WebSocket endpoint для зрителей Mini App.

Авторизация: через httpOnly cookie access_token, отправляемую браузером при handshake.
Никаких дополнительных сообщений от клиента для авторизации не требуется.

Протокол:
  Client → Server: {"type": "pong"}   — ответ на серверный ping
  Client → Server: {"type": "ping"}   — keepalive от клиента (сервер ответит pong)

  Server → Client: {"type": "connected", "viewer_id": ..., "session_id": ...}
  Server → Client: {"type": "ping"}   — каждые PING_INTERVAL сек
  Server → Client: {"type": "pong"}   — ответ на ping от клиента

Коды закрытия:
  4000 — таймаут ping (клиент не ответил pong за PONG_TIMEOUT сек)
  4001 — невалидная или отсутствующая cookie access_token
  4004 — стрим не найден или уже завершён

Присутствие:
  Зритель добавляется в Redis Set stream:viewers:{session_id} после успешного подключения.
  Удаляется при отключении или таймауте ping.
  Passive income task читает из этого Set.
"""
from __future__ import annotations

import asyncio
import contextlib

from dishka.integrations.fastapi import DishkaRoute, FromDishka, inject
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.repos import sql
from src.repos.redis import viewer_presence_repo
from src.services.auth import get_user_from_cookie
from src.services.logger import AbstractLogger, get_logger

router = APIRouter(route_class=DishkaRoute)

logger = get_logger().bind(layer="endpoint", module="ws_viewer")

PING_INTERVAL = 30   # секунд между ping'ами от сервера
PONG_TIMEOUT = 15    # секунд ожидания pong от клиента


@router.websocket("/ws/viewer/{stream_token}")
@inject
async def ws_viewer(
    websocket: WebSocket,
    stream_token: str,
    session_factory: FromDishka[async_sessionmaker[AsyncSession]],
    redis: FromDishka[Redis],
) -> None:
    log = logger.bind(stream_token=stream_token)
    log.debug("viewer ws connection attempt")

    # ── Валидация stream_token ────────────────────────────────────────────────
    async with session_factory() as session:
        async with session.begin():
            stream_session = await sql.stream_sessions_repo.get_by_stream_token(session, stream_token)
            if stream_session is None or not stream_session.is_active:
                log.error("viewer ws: invalid or inactive stream token")
                await websocket.close(code=4004)
                return
            session_id = stream_session.id

    # ── Авторизация через cookie из handshake ─────────────────────────────────
    async with session_factory() as session:
        async with session.begin():
            user = await get_user_from_cookie(
                websocket.cookies.get("access_token"),
                session,
                redis,
            )

    if user is None:
        log.error("viewer ws: invalid or missing cookie")
        await websocket.close(code=4001)
        return

    viewer_id = user.telegram_id
    log = log.bind(viewer_id=viewer_id)

    await websocket.accept()
    log.info("viewer ws authenticated", session_id=session_id)

    # ── Добавляем зрителя в Redis ─────────────────────────────────────────────
    await viewer_presence_repo.add(redis, session_id, viewer_id)
    await websocket.send_json({
        "type": "connected",
        "viewer_id": viewer_id,
        "session_id": session_id,
    })

    # ── Один читающий таск + Event для ping/pong синхронизации ─────────────────
    # Два параллельных receive_json() на одном WebSocket вызывают race condition:
    # pong может быть съеден _client_loop раньше, чем его дождётся _ping_loop.
    # Решение: единый reader, pong сигнализируется через asyncio.Event.
    pong_event = asyncio.Event()

    t_client = asyncio.create_task(_client_loop(websocket, log, pong_event))
    t_ping = asyncio.create_task(_ping_loop(websocket, log, pong_event))

    try:
        done, pending = await asyncio.wait(
            [t_client, t_ping],
            return_when=asyncio.FIRST_COMPLETED,
        )
        for task in pending:
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError, Exception):
                await task
    finally:
        await viewer_presence_repo.remove(redis, session_id, viewer_id)
        log.info("viewer ws disconnected", session_id=session_id)


async def _client_loop(websocket: WebSocket, log: AbstractLogger, pong_event: asyncio.Event) -> None:
    """Единственный читатель WebSocket. Диспетчеризует сообщения по типу."""
    while True:
        try:
            data = await websocket.receive_json()
        except (WebSocketDisconnect, Exception):
            return

        if not isinstance(data, dict):
            continue

        msg_type = data.get("type")
        if msg_type == "ping":
            await websocket.send_json({"type": "pong"})
        elif msg_type == "pong":
            pong_event.set()


async def _ping_loop(websocket: WebSocket, log: AbstractLogger, pong_event: asyncio.Event) -> None:
    """Сервер шлёт ping каждые PING_INTERVAL сек, ждёт pong за PONG_TIMEOUT сек."""
    while True:
        await asyncio.sleep(PING_INTERVAL)

        try:
            await websocket.send_json({"type": "ping"})
        except Exception:
            return

        pong_event.clear()
        try:
            await asyncio.wait_for(pong_event.wait(), timeout=PONG_TIMEOUT)
        except TimeoutError:
            log.info("viewer ping timeout — closing connection")
            with contextlib.suppress(Exception):
                await websocket.close(code=4000)
            return
