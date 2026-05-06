from typing import cast

from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.schemas.dataclasses.settings import StopWordDTO


class StopwordDeleteCallback(CallbackData, prefix="stopword"):
	action: str  # "delete"
	word_id: int


class SettingsKeyboards:
	def settings_menu(self) -> InlineKeyboardMarkup:
		ib = InlineKeyboardBuilder()
		ib.button(text="🚫 Стоп-слова", callback_data="settings:stopwords")
		ib.button(text="🎯 Цель сбора", callback_data="settings:goal")
		ib.button(text="◀️ Назад", callback_data="settings:back")
		return cast(InlineKeyboardMarkup, ib.adjust(2, 1).as_markup())

	def stopwords_menu(self, words: list[StopWordDTO]) -> InlineKeyboardMarkup:
		ib = InlineKeyboardBuilder()
		for w in words:
			ib.button(
				text=f"🗑 {w.word}",
				callback_data=StopwordDeleteCallback(
					action="delete",
					word_id=w.id,
				),
			)
		if words:
			ib.adjust(*([1] * len(words)))
		ib.button(text="➕ Добавить слово", callback_data="stopword:add")
		ib.button(text="◀️ Назад", callback_data="settings:menu")
		return cast(
			InlineKeyboardMarkup,
			ib.adjust(*([1] * len(words)), 2).as_markup(),
		)

	def goal_menu(self) -> InlineKeyboardMarkup:
		ib = InlineKeyboardBuilder()
		ib.button(text="✏️ Изменить цель", callback_data="goal:edit")
		ib.button(text="◀️ Назад", callback_data="settings:menu")
		return cast(InlineKeyboardMarkup, ib.adjust(1, 1).as_markup())

	def cancel(self) -> InlineKeyboardMarkup:
		ib = InlineKeyboardBuilder()
		ib.button(text="❌ Отмена", callback_data="cancel")
		return cast(InlineKeyboardMarkup, ib.adjust(1).as_markup())
