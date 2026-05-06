"""Redis-присутствие зрителей на стриме.

Используется для:
- Отслеживания кто реально смотрит стрим (для пассивного дохода)
- Быстрого подсчёта зрителей без запроса в БД

Структура: Set `stream:viewers:{session_id}` → множество viewer telegram_id (int → str)
"""
from __future__ import annotations

from collections.abc import Awaitable
from typing import cast

from redis.asyncio import Redis

_PREFIX = "stream:viewers:"


def _key(session_id: int) -> str:
    return f"{_PREFIX}{session_id}"


async def add(redis: Redis, session_id: int, viewer_id: int) -> None:
    await cast(Awaitable[int], redis.sadd(_key(session_id), str(viewer_id)))


async def remove(redis: Redis, session_id: int, viewer_id: int) -> None:
    await cast(Awaitable[int], redis.srem(_key(session_id), str(viewer_id)))


async def get_viewer_ids(redis: Redis, session_id: int) -> list[int]:
    members = await cast(Awaitable[set[bytes]], redis.smembers(_key(session_id)))
    return [int(m) for m in members]


async def count(redis: Redis, session_id: int) -> int:
    return await cast(Awaitable[int], redis.scard(_key(session_id)))


async def cleanup(redis: Redis, session_id: int) -> None:
    await cast(Awaitable[int], redis.delete(_key(session_id)))
