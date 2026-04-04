from typing import cast

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
		return cast(InlineKeyboardMarkup, ib.adjust(2).as_markup())

	def viewer_menu(self) -> InlineKeyboardMarkup:
		ib = InlineKeyboardBuilder()
		ib.button(text="🎯 Сделать донат", callback_data="donate:start")
		ib.button(text="💳 Пополнить баланс", callback_data="topup:menu")
		if cfg.app.mini_app_url.startswith("https://"):
			ib.button(
				text="📱 Открыть Mini App",
				web_app=WebAppInfo(url=cfg.app.mini_app_url),
			)
			return cast(InlineKeyboardMarkup, ib.adjust(2, 1).as_markup())
		return cast(InlineKeyboardMarkup, ib.adjust(2).as_markup())

	def streamer_menu(self) -> InlineKeyboardMarkup:
		ib = InlineKeyboardBuilder()
		ib.button(text="▶️ Начать стрим", callback_data="stream:start")
		ib.button(text="⚙️ Настройки", callback_data="settings:menu")
		return cast(InlineKeyboardMarkup, ib.adjust(1).as_markup())
