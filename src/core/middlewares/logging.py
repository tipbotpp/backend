import time
import uuid
from collections.abc import Callable

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
