from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from dishka.integrations.aiogram import FromDishka, inject

from src.bot.keyboards.stream import StreamKeyboards
from src.bot.texts.stream import StreamText
from src.core.exc.exceptions import (
	StreamAlreadyActiveError,
	StreamerRequiredError,
	StreamNotActiveError,
)
from src.models.users import Users
from src.schemas.dataclasses.users import UserDTO
from src.schemas.enums.users import UserRole
from src.services.stream import StreamService, make_widget_url
from src.utils.mappers import map_model

router = Router(name="stream_router")
kb = StreamKeyboards()


@router.message(Command("stream"))
@inject
async def cmd_stream(
	message: Message,
	user: Users,
	stream_service: FromDishka[StreamService],
) -> None:
	if user.role != UserRole.STREAMER:
		await message.answer(StreamText.streamer_only())
		return

	user_dto = map_model(user, UserDTO)
	active = await stream_service.get_status(user_dto)

	if active is None:
		await message.answer(StreamText.inactive(), reply_markup=kb.stream_inactive())
	else:
		widget_url = make_widget_url(active.stream_token)
		await message.answer(
			StreamText.already_active(widget_url, active.started_at),
			reply_markup=kb.stream_active(),
		)


@router.callback_query(F.data == "stream:start")
@inject
async def cb_stream_start(
	callback: CallbackQuery,
	user: Users,
	stream_service: FromDishka[StreamService],
) -> None:
	await callback.answer()
	msg = callback.message
	if not isinstance(msg, Message):
		return

	user_dto = map_model(user, UserDTO)

	try:
		session = await stream_service.start(user_dto, passive_income_enabled=False)
	except StreamerRequiredError:
		await msg.answer("❌ Управление стримом доступно только для стримеров.")
		return
	except StreamAlreadyActiveError:
		active = await stream_service.get_status(user_dto)
		widget_url = make_widget_url(active.stream_token) if active else ""
		await msg.answer(
			StreamText.already_active(widget_url, active.started_at) if active else "Стрим уже активен.",
			reply_markup=kb.stream_active(),
		)
		return

	widget_url = make_widget_url(session.stream_token)
	await msg.answer(StreamText.started(widget_url), reply_markup=kb.stream_active())


@router.callback_query(F.data == "stream:stop")
@inject
async def cb_stream_stop(
	callback: CallbackQuery,
	user: Users,
	stream_service: FromDishka[StreamService],
) -> None:
	await callback.answer()
	msg = callback.message
	if not isinstance(msg, Message):
		return

	user_dto = map_model(user, UserDTO)

	try:
		stopped, stats = await stream_service.stop(user_dto)
	except (StreamNotActiveError, StreamerRequiredError):
		await msg.answer(StreamText.not_active())
		return

	duration = int((stopped.ended_at - stopped.started_at).total_seconds()) if stopped.ended_at else 0
	await msg.answer(
		StreamText.stopped(stats.total_collected, stats.donations_count, duration),
		reply_markup=None,
	)


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
	await message.answer(StreamText.help_text())
