from typing import cast

from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


class TopupAmountCallback(CallbackData, prefix="topup"):
	amount: int


class BalanceKeyboards:
	def topup_menu(self, current_balance: int) -> InlineKeyboardMarkup:
		ib = InlineKeyboardBuilder()
		for amount in (100, 500, 1000):
			ib.button(
				text=f"+{amount}",
				callback_data=TopupAmountCallback(amount=amount),
			)
		ib.button(text="✏️ Другая сумма", callback_data="topup:custom")
		ib.button(text="❌ Отмена", callback_data="cancel")
		return cast(InlineKeyboardMarkup, ib.adjust(3, 1, 1).as_markup())

	def after_topup_menu(self) -> InlineKeyboardMarkup:
		ib = InlineKeyboardBuilder()
		ib.button(text="🎯 Сделать донат", callback_data="donate:start")
		ib.button(text="💳 Пополнить ещё", callback_data="topup:menu")
		return cast(InlineKeyboardMarkup, ib.adjust(2).as_markup())

	def balance_info_menu(self) -> InlineKeyboardMarkup:
		ib = InlineKeyboardBuilder()
		ib.button(text="🎯 Сделать донат", callback_data="donate:start")
		ib.button(text="💳 Пополнить баланс", callback_data="topup:menu")
		return cast(InlineKeyboardMarkup, ib.adjust(2).as_markup())

	def cancel(self) -> InlineKeyboardMarkup:
		ib = InlineKeyboardBuilder()
		ib.button(text="❌ Отмена", callback_data="cancel")
		return cast(InlineKeyboardMarkup, ib.adjust(1).as_markup())
