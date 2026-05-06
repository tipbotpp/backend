import asyncio
from typing import Annotated

from dishka.integrations.fastapi import DishkaRoute, FromDishka, inject
from fastapi import APIRouter, Depends

from src.core.storages import S3Manager
from src.di.deps.auth import CurrentUserDep
from src.repos.s3 import media_repo
from src.schemas.pydantic import donations as donations_schema
from src.services.donations import DonationService
from src.services.logger import get_logger

router = APIRouter(prefix="/donations", route_class=DishkaRoute)

logger = get_logger().bind(layer="endpoint", module="donations")


@router.post(
	"",
	response_model=donations_schema.DonationCreateResponse,
	status_code=201,
	summary="Отправить донат стримеру",
)
@inject
async def send_donation(
	body: donations_schema.DonationBody,
	donation_service: FromDishka[DonationService],
	user: CurrentUserDep,
) -> donations_schema.DonationCreateResponse:
	"""Отправляет донат стримеру от имени зрителя.

	Списывает монеты с баланса, запускает модерацию текста,
	ставит задачи на TTS-озвучку и генерацию изображения в очередь.
	Алерт появится в OBS-виджете после завершения обработки.

	Args:
		body: ID стримера, сумма (1–10 000 монет) и опциональное сообщение (до 500 символов).

	Returns:
		DonationCreateResponse: ID доната и статус `processing`.

	Raises:
		401: Пользователь не аутентифицирован.
		402: Недостаточно монет на балансе.
		403: Только зрители могут отправлять донаты; нельзя донатить самому себе.
		404: Стример не найден или у него нет активного стрима.
		422: Сообщение не прошло модерацию (токсичность или стоп-слово стримера).
	"""
	log = logger.bind(
		request_user_id=user.telegram_id,
		request_streamer_id=body.streamer_id,
		request_amount=body.amount,
		request_message_length=len(body.message) if body.message else 0,
	)
	log.debug("POST /donations")
	donation = await donation_service.send(
		user=user,
		streamer_id=body.streamer_id,
		amount=body.amount,
		message=body.message,
	)
	log.info(
		"donation accepted",
		donation_id=donation.id,
		status=donation.status,
	)
	return donations_schema.DonationCreateResponse(
		donation_id=donation.id,
		status=donation.status,
		message="Донат отправлен и ожидает обработки",
	)


@router.get(
	"/session",
	response_model=donations_schema.SessionStatsResponse,
	summary="Статистика текущей сессии стримера",
)
@inject
async def get_session_stats(
	donation_service: FromDishka[DonationService],
	user: CurrentUserDep,
) -> donations_schema.SessionStatsResponse:
	"""Возвращает статистику донатов текущей активной сессии стрима.

	Включает общую сумму, количество донатов, топ-донатера
	и поминутную динамику для графика.

	Returns:
		SessionStatsResponse: Статистика активной сессии.

	Raises:
		401: Пользователь не аутентифицирован.
		403: Доступно только стримерам.
		404: Нет активного стрима.
	"""
	log = logger.bind(request_user_id=user.telegram_id)
	log.debug("GET /donations/session")
	stats = await donation_service.get_session_stats(user)
	log.debug(
		"session stats retrieved",
		session_id=stats.session_id,
		donations_count=stats.donations_count,
	)
	return donations_schema.SessionStatsResponse(
		session_id=stats.session_id,
		total_collected=stats.total_collected,
		donations_count=stats.donations_count,
		top_donator=(
			donations_schema.TopDonatorResponse(
				username=stats.top_donator.username,
				total_amount=stats.top_donator.total_amount,
			)
			if stats.top_donator
			else None
		),
		timeline=[
			donations_schema.TimelineItemResponse(
				time=item.time,
				amount=item.amount,
			)
			for item in stats.timeline
		],
	)


@router.get(
	"/history",
	response_model=donations_schema.DonationHistoryResponse,
	summary="История донатов пользователя",
)
@inject
async def get_history(
	filters: Annotated[donations_schema.DonationHistoryFilters, Depends()],
	donation_service: FromDishka[DonationService],
	s3: FromDishka[S3Manager],
	user: CurrentUserDep,
) -> donations_schema.DonationHistoryResponse:
	"""Возвращает постраничную историю донатов текущего пользователя.

	Для каждого доната генерируются временные presigned URL на аудио и изображение
	из MinIO (действительны ограниченное время).

	Args:
		filters: Фильтр по направлению (`sent` | `received`) и параметры пагинации.

	Returns:
		DonationHistoryResponse: Список донатов с медиа-ссылками и пагинацией.

	Raises:
		401: Пользователь не аутентифицирован.
	"""
	log = logger.bind(
		request_user_id=user.telegram_id,
		request_type_filter=filters.type,
		request_limit=filters.limit,
		request_offset=filters.offset,
	)
	log.debug("GET /donations/history")
	items, total = await donation_service.get_history(
		user=user,
		type_filter=filters.type,
		limit=filters.limit,
		offset=filters.offset,
	)

	audio_urls, image_urls = await asyncio.gather(
		asyncio.gather(
			*[
				media_repo.resolve_presigned_url(s3, item.audio_key)
				for item in items
			],
		),
		asyncio.gather(
			*[
				media_repo.resolve_presigned_url(s3, item.image_key)
				for item in items
			],
		),
	)

	log.debug("history retrieved", total=total, items_count=len(items))
	return donations_schema.DonationHistoryResponse(
		items=[
			donations_schema.DonationHistoryItemResponse(
				id=item.id,
				amount=item.amount,
				message=item.message,
				status=item.status,
				audio_url=audio_url,
				image_url=image_url,
				from_user=donations_schema.DonorResponse(
					id=item.from_user.id,
					username=item.from_user.username,
				),
				to_streamer=donations_schema.DonorResponse(
					id=item.to_streamer.id,
					username=item.to_streamer.username,
				),
				created_at=item.created_at,
			)
			for item, audio_url, image_url in zip(
				items,
				audio_urls,
				image_urls,
				strict=True,
			)
		],
		total=total,
		limit=filters.limit,
		offset=filters.offset,
	)
