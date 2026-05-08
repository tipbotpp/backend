from typing import cast

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


class StreamKeyboards:
	def stream_inactive(self) -> InlineKeyboardMarkup:
		ib = InlineKeyboardBuilder()
		ib.button(text="▶️ Начать стрим", callback_data="stream:start")
		return cast(InlineKeyboardMarkup, ib.adjust(1).as_markup())

	def stream_active(self) -> InlineKeyboardMarkup:
		ib = InlineKeyboardBuilder()
		ib.button(text="⏹ Остановить стрим", callback_data="stream:stop")
		return cast(InlineKeyboardMarkup, ib.adjust(1).as_markup())
