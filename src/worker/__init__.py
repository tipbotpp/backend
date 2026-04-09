"""arq worker entry point.

Запуск: arq src.worker.WorkerSettings
"""
from arq.connections import RedisSettings

from src.core.configs import cfg
from src.worker.context import shutdown, startup
from src.worker.tasks import process_donation_media


class WorkerSettings:
	functions = [process_donation_media]
	# TODO: добавить passive_income_task в functions и cron_jobs когда будет реализована
	# cron_jobs = [cron(passive_income_task, minute={0, 5, 10, ...})]
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
