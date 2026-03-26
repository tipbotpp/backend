from typing import cast

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


class StartKeyboards:
	def _ib(self) -> InlineKeyboardBuilder:
		return InlineKeyboardBuilder()

	def main(self) -> InlineKeyboardMarkup:
		ib = self._ib()
		ib.button(text="📋 Помощь", callback_data="help")
		return cast(InlineKeyboardMarkup, ib.adjust(1).as_markup())
