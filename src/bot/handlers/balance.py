from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from dishka.integrations.aiogram import FromDishka, inject

from src.bot.keyboards.balance import BalanceKeyboards, TopupAmountCallback
from src.bot.states.topup import TopupStates
from src.bot.texts.balance import BalanceText
from src.models.users import Users
from src.services.balance import BalanceService

router = Router(name="balance_router")
kb = BalanceKeyboards()


@router.message(Command("balance"))
async def cmd_balance(message: Message, user: Users) -> None:
	await message.answer(
		BalanceText.balance_info(user.balance),
		reply_markup=kb.balance_info_menu(),
	)


@router.callback_query(F.data == "topup:menu")
async def cb_topup_menu(callback: CallbackQuery, user: Users) -> None:
	await callback.answer()
	msg = callback.message
	if not isinstance(msg, Message):
		return
	await msg.answer(
		BalanceText.topup_menu(user.balance),
		reply_markup=kb.topup_menu(user.balance),
	)


@router.callback_query(TopupAmountCallback.filter())
@inject
async def cb_topup_amount(
	callback: CallbackQuery,
	callback_data: TopupAmountCallback,
	user: Users,
	balance_service: FromDishka[BalanceService],
) -> None:
	await callback.answer()
	msg = callback.message
	if not isinstance(msg, Message):
		return

	from src.schemas.dataclasses.users import UserDTO
	from src.utils.mappers import map_model
	user_dto = map_model(user, UserDTO)

	_, new_balance = await balance_service.topup(user_dto, callback_data.amount)
	await msg.answer(
		BalanceText.topup_success(callback_data.amount, new_balance),
		reply_markup=kb.after_topup_menu(),
	)


@router.callback_query(F.data == "topup:custom")
async def cb_topup_custom(callback: CallbackQuery, state: FSMContext) -> None:
	await callback.answer()
	msg = callback.message
	if not isinstance(msg, Message):
		return
	await state.set_state(TopupStates.waiting_amount)
	await msg.answer(
		BalanceText.topup_ask_amount(),
		reply_markup=kb.cancel(),
	)


@router.message(TopupStates.waiting_amount)
@inject
async def fsm_topup_amount(
	message: Message,
	state: FSMContext,
	user: Users,
	balance_service: FromDishka[BalanceService],
) -> None:
	text = (message.text or "").strip()
	if not text.isdigit() or int(text) <= 0:
		await message.answer(BalanceText.topup_invalid_amount())
		return

	amount = int(text)
	await state.clear()

	from src.schemas.dataclasses.users import UserDTO
	from src.utils.mappers import map_model
	user_dto = map_model(user, UserDTO)

	_, new_balance = await balance_service.topup(user_dto, amount)
	await message.answer(
		BalanceText.topup_success(amount, new_balance),
		reply_markup=kb.after_topup_menu(),
	)


@router.callback_query(F.data == "cancel")
async def cb_cancel(callback: CallbackQuery, state: FSMContext) -> None:
	await callback.answer()
	await state.clear()
	msg = callback.message
	if not isinstance(msg, Message):
		return
	await msg.answer(BalanceText.cancelled())
