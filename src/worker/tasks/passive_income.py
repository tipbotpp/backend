"""arq cron-таска пассивного дохода.

Запускается каждую минуту. Логика на каждую активную сессию с passive_income_enabled=True:
1. Получить PassiveIncomeSettings стримера (coins_per_interval, interval_minutes).
2. Атомарный SET NX с TTL=interval_seconds — только один воркер в одном интервале пройдёт.
3. Прочитать список зрителей из Redis Set stream:viewers:{session_id}.
   Туда добавляются зрители при подключении viewer WS и удаляются при отключении.
4. Начислить каждому зрителю coins_per_interval атомарным инкрементом.
5. Записать BalanceTransaction.
6. Отправить Telegram-уведомление.
"""
from __future__ import annotations

from aiogram import Bot
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import async_sessionmaker

from src.repos import sql
from src.repos.redis import viewer_presence_repo
from src.schemas.dataclasses.balance import BalanceTransactionCreateDTO
from src.schemas.enums.balance import BalanceTransactionType
from src.services.logger import get_logger

logger = get_logger().bind(layer="worker", module="passive_income")

_COOLDOWN_PREFIX = "pi:cooldown:"
_DEFAULT_COINS = 10
_DEFAULT_INTERVAL_MINUTES = 5


def _cooldown_key(session_id: int) -> str:
    return f"{_COOLDOWN_PREFIX}{session_id}"


async def passive_income_task(ctx: dict) -> None:
    """Cron-таска: начислить пассивный доход зрителям всех активных стримов."""
    session_factory: async_sessionmaker = ctx["session_factory"]
    redis: Redis = ctx["redis"]
    bot: Bot = ctx["bot"]

    log = logger.bind()
    log.info("passive_income_task started")

    async with session_factory() as session:
        async with session.begin():
            active_sessions = await sql.stream_sessions_repo.get_all_active_with_passive_income(session)

    if not active_sessions:
        log.debug("passive_income_task: no active sessions with passive income")
        return

    log.info("active passive income sessions", count=len(active_sessions))

    for stream_session in active_sessions:
        session_log = log.bind(session_id=stream_session.id)

        # ── 1. Получаем настройки СНАЧАЛА — они нужны для TTL cooldown ────────
        async with session_factory() as session:
            async with session.begin():
                pi_settings = await sql.passive_income_settings_repo.get_by_streamer_id(
                    session, stream_session.streamer_id,
                )
                streamer = await sql.users_repo.get_by_telegram_id(
                    session, stream_session.streamer_id,
                )

        coins = pi_settings.coins_per_interval if pi_settings else _DEFAULT_COINS
        interval_seconds = (
            pi_settings.interval_minutes if pi_settings else _DEFAULT_INTERVAL_MINUTES
        ) * 60

        # ── 2. Атомарный SET NX: только один воркер пройдёт за интервал ───────
        acquired = await redis.set(
            _cooldown_key(stream_session.id), "1", ex=interval_seconds, nx=True,
        )
        if not acquired:
            session_log.debug("passive income cooldown active")
            continue

        # ── 3. Зрители из Redis presence ─────────────────────────────────────
        viewer_ids = await viewer_presence_repo.get_viewer_ids(redis, stream_session.id)
        if not viewer_ids:
            session_log.debug("no viewers connected, skipping payout")
            continue

        streamer_name = (
            streamer.display_name or streamer.username or "Стримера"
            if streamer else "Стримера"
        )

        session_log.info("crediting passive income", coins=coins, viewers_count=len(viewer_ids))

        # ── 4-6. Начисляем каждому зрителю ───────────────────────────────────
        for viewer_id in viewer_ids:
            try:
                async with session_factory() as session:
                    async with session.begin():
                        # Атомарный инкремент — нет race condition с параллельными воркерами
                        new_balance = await sql.users_repo.increment_balance(
                            session, viewer_id, coins,
                        )
                        if new_balance is None:
                            session_log.error("viewer not found in db", viewer_id=viewer_id)
                            continue
                        await sql.balance_transactions_repo.create(
                            session,
                            BalanceTransactionCreateDTO(
                                user_id=viewer_id,
                                amount=coins,
                                type=BalanceTransactionType.PASSIVE_INCOME,
                            ),
                        )

                try:
                    await bot.send_message(
                        chat_id=viewer_id,
                        text=(
                            f"🎁 <b>+{coins} монет</b> за просмотр стрима {streamer_name}!\n"
                            f"Текущий баланс: {new_balance} монет"
                        ),
                    )
                except Exception as e:
                    session_log.error("notification failed", viewer_id=viewer_id, error=str(e))

            except Exception as e:
                session_log.error("credit failed", viewer_id=viewer_id, error=str(e))

        session_log.info("passive income payout done", interval_seconds=interval_seconds)

    log.info("passive_income_task done")
