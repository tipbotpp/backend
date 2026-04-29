from __future__ import annotations

import contextlib

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from dishka.integrations.aiogram import FromDishka, inject

from src.bot.keyboards.settings import (
    SettingsKeyboards,
    StopwordDeleteCallback,
)
from src.bot.states.settings import GoalStates, StopwordStates
from src.bot.texts.settings import SettingsText
from src.core.exc.exceptions import ConflictError, NotFoundError
from src.models.users import Users
from src.schemas.dataclasses.users import UserDTO
from src.schemas.enums.users import UserRole
from src.services.settings import SettingsService
from src.utils.mappers import map_model

router = Router(name="settings_router")
kb = SettingsKeyboards()


def _user_dto(user: Users) -> UserDTO:
    return map_model(user, UserDTO)


def _is_streamer(user: Users) -> bool:
    return user.role == UserRole.STREAMER


# ── /settings команда и главное меню ─────────────────────────────────────────

@router.message(Command("settings"))
async def cmd_settings(message: Message, user: Users) -> None:
    if not _is_streamer(user):
        await message.answer(SettingsText.streamer_only())
        return
    await message.answer(SettingsText.menu(), reply_markup=kb.settings_menu())


@router.callback_query(F.data == "settings:menu")
async def cb_settings_menu(callback: CallbackQuery, user: Users) -> None:
    await callback.answer()
    msg = callback.message
    if not isinstance(msg, Message):
        return
    if not _is_streamer(user):
        await msg.answer(SettingsText.streamer_only())
        return
    await msg.edit_text(SettingsText.menu(), reply_markup=kb.settings_menu())


@router.callback_query(F.data == "settings:back")
async def cb_settings_back(callback: CallbackQuery, user: Users) -> None:
    """Возврат — показываем стандартное меню стримера."""
    await callback.answer()
    msg = callback.message
    if not isinstance(msg, Message):
        return
    from src.bot.keyboards.start import StartKeyboards  # noqa: PLC0415
    await msg.edit_text(
        "👋 Главное меню",
        reply_markup=StartKeyboards().streamer_menu(),
    )


# ── Стоп-слова ────────────────────────────────────────────────────────────────

@router.callback_query(F.data == "settings:stopwords")
@inject
async def cb_stopwords(
    callback: CallbackQuery,
    user: Users,
    settings_service: FromDishka[SettingsService],
) -> None:
    await callback.answer()
    msg = callback.message
    if not isinstance(msg, Message):
        return
    words = await settings_service.get_stopwords(_user_dto(user))
    await msg.edit_text(
        SettingsText.stopwords_list(words),
        reply_markup=kb.stopwords_menu(words),
    )


@router.callback_query(F.data == "stopword:add")
async def cb_stopword_add(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    msg = callback.message
    if not isinstance(msg, Message):
        return
    await state.set_state(StopwordStates.waiting_word)
    await msg.answer(SettingsText.stopword_ask(), reply_markup=kb.cancel())


@router.message(StopwordStates.waiting_word)
@inject
async def fsm_stopword_word(
    message: Message,
    state: FSMContext,
    user: Users,
    settings_service: FromDishka[SettingsService],
) -> None:
    word = (message.text or "").strip()
    if not word:
        await message.answer(SettingsText.stopword_empty(), reply_markup=kb.cancel())
        return

    await state.clear()

    try:
        result = await settings_service.add_stopword(_user_dto(user), word)
    except ConflictError:
        await message.answer(SettingsText.stopword_duplicate(word))
        return

    await message.answer(SettingsText.stopword_added(result.word))

    # Обновляем список
    words = await settings_service.get_stopwords(_user_dto(user))
    await message.answer(
        SettingsText.stopwords_list(words),
        reply_markup=kb.stopwords_menu(words),
    )


@router.callback_query(StopwordDeleteCallback.filter(F.action == "delete"))
@inject
async def cb_stopword_delete(
    callback: CallbackQuery,
    callback_data: StopwordDeleteCallback,
    user: Users,
    settings_service: FromDishka[SettingsService],
) -> None:
    await callback.answer()
    msg = callback.message
    if not isinstance(msg, Message):
        return

    with contextlib.suppress(NotFoundError, Exception):
        await settings_service.delete_stopword(
            _user_dto(user), callback_data.word_id,
        )

    words = await settings_service.get_stopwords(_user_dto(user))
    await msg.edit_text(
        SettingsText.stopwords_list(words),
        reply_markup=kb.stopwords_menu(words),
    )


# ── Цель сбора ────────────────────────────────────────────────────────────────

@router.callback_query(F.data == "settings:goal")
@inject
async def cb_goal(
    callback: CallbackQuery,
    user: Users,
    settings_service: FromDishka[SettingsService],
) -> None:
    await callback.answer()
    msg = callback.message
    if not isinstance(msg, Message):
        return
    goal = await settings_service.get_goal(_user_dto(user))
    await msg.edit_text(
        SettingsText.goal_info(goal),
        reply_markup=kb.goal_menu(),
    )


@router.callback_query(F.data == "goal:edit")
async def cb_goal_edit(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    msg = callback.message
    if not isinstance(msg, Message):
        return
    await state.set_state(GoalStates.waiting_title)
    await msg.answer(SettingsText.goal_ask_title(), reply_markup=kb.cancel())


@router.message(GoalStates.waiting_title)
async def fsm_goal_title(message: Message, state: FSMContext) -> None:
    title = (message.text or "").strip()
    if not title:
        await message.answer(SettingsText.goal_ask_title(), reply_markup=kb.cancel())
        return
    await state.update_data(title=title)
    await state.set_state(GoalStates.waiting_amount)
    await message.answer(SettingsText.goal_ask_amount(title), reply_markup=kb.cancel())


@router.message(GoalStates.waiting_amount)
@inject
async def fsm_goal_amount(
    message: Message,
    state: FSMContext,
    user: Users,
    settings_service: FromDishka[SettingsService],
) -> None:
    text = (message.text or "").strip()
    if not text.isdigit() or int(text) <= 0:
        await message.answer(SettingsText.goal_invalid_amount(), reply_markup=kb.cancel())
        return

    amount = int(text)
    data = await state.get_data()
    title = data.get("title", "")
    await state.clear()

    await settings_service.update_goal(_user_dto(user), title=title, target_amount=amount)
    await message.answer(SettingsText.goal_updated(title, amount))
