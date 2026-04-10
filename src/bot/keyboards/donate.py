from typing import cast

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


class DonateKeyboards:
	def cancel(self) -> InlineKeyboardMarkup:
		ib = InlineKeyboardBuilder()
		ib.button(text="❌ Отмена", callback_data="cancel")
		return cast(InlineKeyboardMarkup, ib.adjust(1).as_markup())

	def skip_message(self) -> InlineKeyboardMarkup:
		ib = InlineKeyboardBuilder()
		ib.button(text="Без сообщения", callback_data="donate:skip_message")
		ib.button(text="❌ Отмена", callback_data="cancel")
		return cast(InlineKeyboardMarkup, ib.adjust(1).as_markup())
