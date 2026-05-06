import time
import uuid
from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Update
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from src.services.logger.logger import (
	get_logger,
	http_layer,
	http_method,
	http_path,
	http_request_id,
)


class HTTPLoggingMiddleware(BaseHTTPMiddleware):
	"""Middleware для автоматического логирования HTTP запросов и установки контекста"""

	async def dispatch(
		self,
		request: Request,
		call_next: Callable,
	) -> Response:
		# Генерируем уникальный ID запроса
		request_id = str(uuid.uuid4())[:8]

		# Устанавливаем контекст для логов
		http_path.set(str(request.url.path))
		http_method.set(request.method)
		http_layer.set("http")
		http_request_id.set(request_id)

		# Создаем logger через нашу систему фильтрации
		logger = get_logger().bind(middleware="http")
		start_time = time.time()

		# Логируем начало запроса
		if request.query_params:
			logger.debug(
				"HTTP request started",
				query_params=str(request.query_params),
			)
		else:
			logger.debug("HTTP request started")

		try:
			# Обрабатываем запрос
			response = await call_next(request)

			# Вычисляем время обработки
			process_time = time.time() - start_time

			# Логируем успешное завершение
			logger.info(
				"HTTP request completed",
				status_code=response.status_code,
				process_time_seconds=round(process_time, 4),
			)

			return response

		except Exception:
			# Не логируем исключения здесь - это делают exception handlers
			# Просто перебрасываем исключение
			raise


class LoggingMiddleware(BaseMiddleware):
	"""Middleware для логирования входящих update'ов aiogram."""

	async def __call__(
		self,
		handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
		event: TelegramObject,
		data: dict[str, Any],
	) -> Any:
		logger = get_logger().bind(middleware="telegram")
		start_time = time.time()

		update_type = "unknown"
		user_id = None

		if isinstance(event, Update):
			if event.message:
				update_type = "message"
				user_id = (
					event.message.from_user.id
					if event.message.from_user
					else None
				)
			elif event.callback_query:
				update_type = "callback_query"
				user_id = event.callback_query.from_user.id
			elif event.inline_query:
				update_type = "inline_query"
				user_id = event.inline_query.from_user.id

		logger.debug(
			"Update received",
			update_type=update_type,
			user_id=user_id,
		)

		try:
			result = await handler(event, data)
			process_time = time.time() - start_time
			logger.info(
				"Update handled",
				update_type=update_type,
				user_id=user_id,
				process_time_seconds=round(process_time, 4),
			)
			return result
		except Exception:
			raise
