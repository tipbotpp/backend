from aiogram import Router

from .example import build_start_router

router = Router(name="main_router")
router.include_router(build_start_router())
