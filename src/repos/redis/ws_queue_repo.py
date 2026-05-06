"""Redis-очередь для координации arq worker ↔ FastAPI WS handler.

Два типа сообщений в одном BLPOP:
  ws:jobs:{token}    — job_id от arq (новый донат обработан)
  ws:control:{token} — управляющие события (stream_stopped, test_alert)
"""
from __future__ import annotations

import json
from collections.abc import Awaitable
from typing import cast

from redis.asyncio import Redis

_JOBS_PREFIX = "ws:jobs:"
_CONTROL_PREFIX = "ws:control:"


def jobs_key(stream_token: str) -> str:
	return f"{_JOBS_PREFIX}{stream_token}"


def control_key(stream_token: str) -> str:
	return f"{_CONTROL_PREFIX}{stream_token}"


async def push_job_id(redis: Redis, stream_token: str, job_id: str) -> None:
	"""Положить job_id в очередь после enqueue_job."""
	await cast(Awaitable[int], redis.lpush(jobs_key(stream_token), job_id))


async def push_control(redis: Redis, stream_token: str, event: dict) -> None:
	"""Положить управляющее событие (stream_stopped, test_alert и т.д.)."""
	await cast(Awaitable[int], redis.lpush(control_key(stream_token), json.dumps(event, ensure_ascii=False)))


async def pop_next(
	redis: Redis,
	stream_token: str,
	timeout: int = 30,
) -> tuple[str, str] | tuple[None, None]:
	"""BLPOP из обеих очередей. Возвращает ("job"|"control", value) или (None, None) по таймауту."""
	result = await cast(
		Awaitable[list[bytes] | None],
		redis.blpop([jobs_key(stream_token), control_key(stream_token)], timeout=timeout),
	)
	if result is None:
		return None, None
	key, value = result
	key_str = key.decode() if isinstance(key, bytes) else key
	value_str = value.decode() if isinstance(value, bytes) else value
	queue_type = "job" if key_str == jobs_key(stream_token) else "control"
	return queue_type, value_str


async def cleanup(redis: Redis, stream_token: str) -> None:
	"""Удалить очереди при завершении стрима."""
	await cast(Awaitable[int], redis.delete(jobs_key(stream_token), control_key(stream_token)))
