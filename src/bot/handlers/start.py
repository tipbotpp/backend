from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import CallbackQuery, Message
from dishka.integrations.aiogram import FromDishka, inject
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.keyboards.start import RoleCallback, StartKeyboards
from src.bot.texts.start import StartText
from src.models.users import Users
from src.repos import sql
from src.schemas.enums.users import UserRole

router = Router(name="start_router")
kb = StartKeyboards()

_VIEWER_START_BALANCE = 100


@router.message(CommandStart())
async def cmd_start(message: Message, user: Users) -> None:
	if message.from_user is None:
		return

	name = message.from_user.first_name or message.from_user.username or "друг"

	if user.role is None:
		await message.answer(
			StartText.welcome_new(name),
			reply_markup=kb.role_selection(),
			parse_mode="HTML",
		)
	elif user.role == UserRole.VIEWER:
		await message.answer(
			StartText.welcome_viewer(name),
			reply_markup=kb.viewer_menu(),
			parse_mode="HTML",
		)
	else:
		await message.answer(
			StartText.welcome_streamer(name),
			reply_markup=kb.streamer_menu(),
			parse_mode="HTML",
		)


@router.callback_query(RoleCallback.filter())
@inject
async def cb_select_role(
	callback: CallbackQuery,
	callback_data: RoleCallback,
	user: Users,
	session: FromDishka[AsyncSession],
) -> None:
	await callback.answer()

	msg = callback.message
	if not isinstance(msg, Message):
		return

	if user.role is not None:
		await msg.edit_text(
			StartText.role_already_set(),
			reply_markup=None,
		)
		return

	try:
		role = UserRole(callback_data.value)
	except ValueError:
		return

	new_balance = _VIEWER_START_BALANCE if role is UserRole.VIEWER else None

	await sql.users_repo.update_role(
		session,
		user.telegram_id,
		role.value,
		balance=new_balance,
	)

	if role is UserRole.VIEWER:
		await msg.edit_text(
			StartText.role_set_viewer(),
			reply_markup=StartKeyboards().viewer_menu(),
			parse_mode="HTML",
		)
	else:
		await msg.edit_text(
			StartText.role_set_streamer(),
			reply_markup=StartKeyboards().streamer_menu(),
			parse_mode="HTML",
		)
