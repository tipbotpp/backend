from aiogram import Router

from src.bot.handlers.balance import router as balance_router
from src.bot.handlers.donate import router as donate_router
from src.bot.handlers.start import router as start_router
from src.bot.handlers.stream import router as stream_router

# TODO: добавить settings_router — /settings, стоп-слова (FSM), цель сбора

router = Router(name="main_router")
router.include_router(start_router)
router.include_router(balance_router)
router.include_router(donate_router)
router.include_router(stream_router)
