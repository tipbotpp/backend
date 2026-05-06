import asyncio
from typing import Any

import pytest


@pytest.mark.asyncio
async def test_concurrent_donations(
	donation_service: Any,
	user: Any,
	streamer: Any,
) -> None:
	tasks: list[asyncio.Future[Any]] = []

	for _ in range(20):
		tasks.append(
			donation_service.send(
				user=user,
				streamer_id=streamer.telegram_id,
				amount=10,
				message="race",
			),
		)

	results = await asyncio.gather(*tasks, return_exceptions=True)

	errors = [r for r in results if isinstance(r, Exception)]
	assert len(errors) == 0
