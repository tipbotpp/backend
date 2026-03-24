from aiogram import Router

from src.bot.handlers.start import router as start_router

router = Router(name="main_router")
router.include_router(start_router)
