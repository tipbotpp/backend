from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from dishka.integrations.aiogram import FromDishka, inject
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.keyboards.donate import DonateKeyboards
from src.bot.states.donate import DonateStates
from src.bot.texts.donate import DonateText
from src.core.exc.exceptions import (
	InsufficientBalanceError,
	StreamNotActiveError,
	UserNotFoundError,
)
from src.models.users import Users
from src.repos import sql
from src.schemas.dataclasses.users import UserDTO
from src.services.donations import DonationService
from src.utils.mappers import map_model

router = Router(name="donate_router")
kb = DonateKeyboards()


@router.callback_query(F.data == "donate:start")
async def cb_donate_start(callback: CallbackQuery, state: FSMContext) -> None:
	await callback.answer()
	msg = callback.message
	if not isinstance(msg, Message):
		return
	await state.set_state(DonateStates.waiting_streamer_id)
	await msg.answer(
		DonateText.ask_streamer(),
		reply_markup=kb.cancel(),
	)


@router.message(DonateStates.waiting_streamer_id)
@inject
async def fsm_streamer_id(
	message: Message,
	state: FSMContext,
	user: Users,
	session: FromDishka[AsyncSession],
) -> None:
	text = (message.text or "").strip().lstrip("@")

	if text.isdigit():
		streamer = await sql.users_repo.get_by_telegram_id(session, int(text))
	else:
		streamer = await sql.users_repo.get_by_username(session, text)

	if streamer is None or streamer.role != "streamer":
		await message.answer(DonateText.streamer_not_found(), reply_markup=kb.cancel())
		return

	active_session = await sql.stream_sessions_repo.get_active_by_streamer_id(session, streamer.telegram_id)
	if active_session is None:
		streamer_name = streamer.display_name or streamer.username or str(streamer.telegram_id)
		await message.answer(
			DonateText.streamer_no_active_stream(streamer_name),
			reply_markup=kb.cancel(),
		)
		return

	streamer_name = streamer.display_name or streamer.username or str(streamer.telegram_id)
	await state.update_data(streamer_id=streamer.telegram_id, streamer_name=streamer_name)
	await state.set_state(DonateStates.waiting_amount)
	await message.answer(
		DonateText.ask_amount(streamer_name, user.balance),
		reply_markup=kb.cancel(),
	)


@router.message(DonateStates.waiting_amount)
async def fsm_donate_amount(message: Message, state: FSMContext, user: Users) -> None:
	text = (message.text or "").strip()
	if not text.isdigit() or int(text) <= 0:
		await message.answer(DonateText.invalid_amount())
		return

	amount = int(text)
	if user.balance < amount:
		await message.answer(
			DonateText.not_enough_balance(amount, user.balance),
			reply_markup=kb.cancel(),
		)
		return

	await state.update_data(amount=amount)
	await state.set_state(DonateStates.waiting_message)
	await message.answer(
		DonateText.ask_message(),
		reply_markup=kb.skip_message(),
	)


@router.callback_query(F.data == "donate:skip_message", DonateStates.waiting_message)
@inject
async def cb_skip_message(
	callback: CallbackQuery,
	state: FSMContext,
	user: Users,
	donation_service: FromDishka[DonationService],
) -> None:
	await callback.answer()
	msg = callback.message
	if not isinstance(msg, Message):
		return
	await _send_donation(msg, state, user, donation_service, message_text=None)


@router.message(DonateStates.waiting_message)
@inject
async def fsm_donate_message(
	message: Message,
	state: FSMContext,
	user: Users,
	donation_service: FromDishka[DonationService],
) -> None:
	await _send_donation(message, state, user, donation_service, message_text=message.text)


async def _send_donation(
	message: Message,
	state: FSMContext,
	user: Users,
	donation_service: DonationService,
	message_text: str | None,
) -> None:
	data = await state.get_data()
	streamer_id: int = data["streamer_id"]
	streamer_name: str = data["streamer_name"]
	amount: int = data["amount"]
	await state.clear()

	user_dto = map_model(user, UserDTO)

	try:
		await donation_service.send(
			user=user_dto,
			streamer_id=streamer_id,
			amount=amount,
			message=message_text,
		)
	except InsufficientBalanceError:
		await message.answer(DonateText.not_enough_balance(amount, user.balance))
		return
	except (UserNotFoundError, StreamNotActiveError):
		await message.answer(DonateText.streamer_no_active_stream(streamer_name))
		return

	await message.answer(DonateText.success(streamer_name))
	# Уведомление стримеру отправляет arq-воркер после обработки TTS/Image
