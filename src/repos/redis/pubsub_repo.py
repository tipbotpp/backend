from __future__ import annotations

import json

from redis.asyncio import Redis

_CHANNEL_PREFIX = "ws:"


def channel_key(stream_token: str) -> str:
	return f"{_CHANNEL_PREFIX}{stream_token}"


async def publish(redis: Redis, stream_token: str, event: dict) -> None:
	"""Опубликовать JSON-событие в канал WebSocket-стримера."""
	await redis.publish(channel_key(stream_token), json.dumps(event, ensure_ascii=False))
