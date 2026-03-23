from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardMarkup, WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.core.configs import cfg


class RoleCallback(CallbackData, prefix="role"):
	value: str


class StartKeyboards:
	def role_selection(self) -> InlineKeyboardMarkup:
		ib = InlineKeyboardBuilder()
		ib.button(
			text="🎬 Я стример",
			callback_data=RoleCallback(value="streamer"),
		)
		ib.button(
			text="👀 Я зритель",
			callback_data=RoleCallback(value="viewer"),
		)
		return ib.adjust(2).as_markup()

	def viewer_menu(self) -> InlineKeyboardMarkup:
		ib = InlineKeyboardBuilder()
		ib.button(
			text="🚀 Открыть TipBot",
			web_app=WebAppInfo(url=cfg.app.mini_app_url),
		)
		return ib.adjust(1).as_markup()

	def streamer_menu(self) -> InlineKeyboardMarkup:
		ib = InlineKeyboardBuilder()
		ib.button(text="▶️ Начать стрим", callback_data="stream:start")
		ib.button(text="⚙️ Настройки", callback_data="settings:menu")
		return ib.adjust(1).as_markup()
