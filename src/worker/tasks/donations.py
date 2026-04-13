"""arq-таска обработки медиа-артефактов доната.

Последовательность:
1. TTS (если включён и есть текст)
2. Image generation (если включён и есть текст) — пока заглушка
3. Обновить донат в БД (audio_key, image_key, status=delivered)
4. Сформировать presigned URLs для audio и image
5. Опубликовать new_alert в WebSocket-канал стримера
6. Опубликовать goal_updated (если у стримера есть цель)
7. Telegram-уведомление стримеру
"""
import asyncio
import json

import httpx
from aiogram import Bot
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import async_sessionmaker

from src.core.storages import S3Manager
from src.gateways import ml as ml_gateway
from src.repos import sql
from src.repos.s3 import media_repo
from src.repos.redis import pubsub_repo
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
	stream_token: str,
	alert_bg_color: str,
	alert_text_color: str,
	alert_font: str,
	alert_duration_sec: int,
) -> None:
	log = logger.bind(
		donation_id=donation_id,
		donor_name=donor_name,
		request_amount=amount,
		tts_enabled=tts_enabled,
		image_enabled=image_enabled,
		stream_token=stream_token,
	)
	log.info("process_donation_media started")

	session_factory: async_sessionmaker = ctx["session_factory"]
	ml_client: httpx.AsyncClient = ctx["ml_client"]
	bot: Bot = ctx["bot"]
	redis_client: Redis = ctx["redis_client"]
	s3_manager: S3Manager = ctx["s3_manager"]

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

	# ── Presigned URLs ────────────────────────────────────────────────────────
	audio_url, image_url = await asyncio.gather(
		media_repo.resolve_presigned_url(s3_manager, audio_key),
		media_repo.resolve_presigned_url(s3_manager, image_key),
		return_exceptions=True,
	)
	if isinstance(audio_url, BaseException):
		log.error("audio presign failed", error=str(audio_url))
		audio_url = None
	if isinstance(image_url, BaseException):
		log.error("image presign failed", error=str(image_url))
		image_url = None

	# ── WebSocket: new_alert ──────────────────────────────────────────────────
	alert_event = {
		"type": "new_alert",
		"donation_id": donation_id,
		"donor_name": donor_name,
		"amount": amount,
		"message": text,
		"audio_url": audio_url,
		"image_url": image_url,
		"style": {
			"bg_color": alert_bg_color,
			"text_color": alert_text_color,
			"font": alert_font,
			"duration_sec": alert_duration_sec,
		},
	}
	try:
		await pubsub_repo.publish(redis_client, stream_token, alert_event)
		log.info("new_alert published", stream_token=stream_token)
	except Exception as e:
		log.error("ws publish new_alert failed", error=str(e))

	# ── WebSocket: goal_updated ───────────────────────────────────────────────
	try:
		async with session_factory() as session:
			async with session.begin():
				goal = await sql.stream_goals_repo.get_by_streamer_id(session, streamer_id)

		if goal and goal.target_amount > 0:
			percent = round(goal.current_amount / goal.target_amount * 100)
			goal_event = {
				"type": "goal_updated",
				"title": goal.title,
				"target_amount": goal.target_amount,
				"current_amount": goal.current_amount,
				"percent": percent,
			}
			await pubsub_repo.publish(redis_client, stream_token, goal_event)
			log.info("goal_updated published")
	except Exception as e:
		log.error("ws publish goal_updated failed", error=str(e))

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
