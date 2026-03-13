from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.types import CallbackQuery, Message

from src.bot.keyboards.example import StartKeyboards
from src.bot.texts.example import StartText


def build_start_router() -> Router:
	router = Router(name="start_router")
	kb = StartKeyboards()

	@router.message(CommandStart())
	async def cmd_start(message: Message) -> None:
		name = message.from_user.first_name if message.from_user else "друг"
		await message.answer(
			StartText.greeting(name),
			reply_markup=kb.main(),
		)

	@router.message(Command("help"))
	async def cmd_help(message: Message) -> None:
		await message.answer(StartText.help(), parse_mode="HTML")

	@router.callback_query(lambda c: c.data == "help")
	async def cb_help(callback: CallbackQuery) -> None:
		await callback.answer()
		if callback.message:
			await callback.message.answer(
				StartText.help(),
				parse_mode="HTML",
			)

	return router
