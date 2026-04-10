"""arq-таска обработки медиа-артефактов доната.

Последовательность:
1. TTS (если включён и есть текст)
2. Image generation (если включён и есть текст) — пока заглушка
3. Обновить донат в БД (audio_key, image_key, status=delivered)
4. WebSocket push стримеру — TODO: реализовать в спринте WS
5. Telegram-уведомление стримеру
"""
import asyncio

import httpx
from aiogram import Bot
from sqlalchemy.ext.asyncio import async_sessionmaker

from src.gateways import ml as ml_gateway
from src.repos import sql
from src.schemas.dataclasses.ml import ImageRequestDTO, TTSRequestDTO
from src.services.logger import get_logger

logger = get_logger().bind(layer="worker", module="donations")


async def process_donation_media(
	ctx: dict,
	*,
	donation_id: int,
	text: str | None,
	donor_name: str,
	amount: int,
	voice: str,
	tts_enabled: bool,
	image_enabled: bool,
	streamer_id: int,
) -> None:
	log = logger.bind(
		donation_id=donation_id,
		donor_name=donor_name,
		request_amount=amount,
		tts_enabled=tts_enabled,
		image_enabled=image_enabled,
	)
	log.info("process_donation_media started")

	session_factory: async_sessionmaker = ctx["session_factory"]
	ml_client: httpx.AsyncClient = ctx["ml_client"]
	bot: Bot = ctx["bot"]

	audio_key: str | None = None
	image_key: str | None = None

	# ── Медиа: TTS + Image параллельно ──────────────────────────────────────
	media_tasks = []

	if tts_enabled and text:
		media_tasks.append(
			ml_gateway.synthesize_tts(
				ml_client,
				TTSRequestDTO(
					text=text,
					donor_name=donor_name,
					amount=amount,
					voice=voice,
					donation_id=donation_id,
				),
			),
		)
	else:
		media_tasks.append(asyncio.sleep(0))

	if image_enabled and text:
		media_tasks.append(
			ml_gateway.generate_image(
				ml_client,
				ImageRequestDTO(
					text=text,
					donor_name=donor_name,
					amount=amount,
					donation_id=donation_id,
				),
			),
		)
	else:
		media_tasks.append(asyncio.sleep(0))

	tts_result, image_result = await asyncio.gather(*media_tasks, return_exceptions=True)

	if isinstance(tts_result, BaseException):
		log.error("tts failed", error=str(tts_result))
	else:
		audio_key = tts_result.audio_key
		log.info("tts done", audio_key=audio_key)

	if isinstance(image_result, BaseException):
		log.debug("image skipped or failed", error=str(image_result))
	else:
		image_key = image_result.image_key
		log.info("image done", image_key=image_key)

	# ── Обновить донат ───────────────────────────────────────────────────────
	async with session_factory() as session:
		async with session.begin():
			await sql.donations_repo.update_ml_artifacts(
				session,
				donation_id,
				audio_url=audio_key,
				image_url=image_key,
				status="delivered",
			)
	log.info("donation updated", status="delivered")

	# TODO: отправить new_alert в WebSocket стримера после реализации WS-эндпоинта
	# await ws_manager.push_alert(streamer_id, {
	#     "type": "new_alert",
	#     "donation_id": donation_id,
	#     "donor_name": donor_name,
	#     "amount": amount,
	#     "message": text,
	#     "audio_url": audio_key,
	#     "image_url": image_key,
	# })

	# ── Telegram-уведомление стримеру ────────────────────────────────────────
	notification = _build_notification(donor_name, amount, text)
	try:
		await bot.send_message(chat_id=streamer_id, text=notification)
		log.info("streamer notified", streamer_id=streamer_id)
	except Exception as e:
		log.error("telegram notification failed", error=str(e))

	log.info("process_donation_media done")


def _build_notification(donor_name: str, amount: int, text: str | None) -> str:
	lines = [
		"💰 <b>Новый донат!</b>",
		"",
		f"От: {donor_name}",
		f"Сумма: {amount} монет",
	]
	if text:
		lines.append(f"Сообщение: «{text}»")
	return "\n".join(lines)
