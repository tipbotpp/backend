"""arq worker entry point.

Запуск: arq src.worker.WorkerSettings
"""

from arq import cron
from arq.connections import RedisSettings

from src.core.configs import cfg
from src.worker.context import shutdown, startup
from src.worker.tasks import passive_income_task, process_donation_media


class WorkerSettings:
	functions = [process_donation_media]
	# Запускается каждую минуту; фактический интервал пейаута контролируется
	# Redis-cooldown внутри passive_income_task (interval_minutes из PassiveIncomeSettings)
	cron_jobs = [cron(passive_income_task, minute=set(range(60)))]
	on_startup = startup
	on_shutdown = shutdown
	redis_settings = RedisSettings(
		host=cfg.redis.host,
		port=cfg.redis.port,
		database=cfg.redis.db,
		password=cfg.redis.password,
	)
	max_jobs = 10
	job_timeout = 120  # секунд на одну задачу
