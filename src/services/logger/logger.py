# ruff: noqa: ANN001, ANN002, ANN202, ARG001, ANN401
from __future__ import annotations

from contextvars import ContextVar
from typing import Any, cast

import structlog

from src.core.config import cfg
from src.services.logger.interfaces import AbstractLogger

# Контекстные переменные для HTTP-запросов
http_path: ContextVar[str] = ContextVar("http_path", default="")
http_method: ContextVar[str] = ContextVar("http_method", default="")
http_layer: ContextVar[str] = ContextVar("http_layer", default="http")
http_request_id: ContextVar[str] = ContextVar("http_request_id", default="")


def http_context_processor(
	logger: Any,
	method_name: str,
	event_dict: dict[str, Any],
) -> dict[str, Any]:
	"""Добавляет HTTP-контекст в логи."""
	path = http_path.get("")
	method = http_method.get("")
	layer = http_layer.get("http")
	request_id = http_request_id.get("")

	if path:
		event_dict["path"] = path
	if method:
		event_dict["method"] = method
	if layer:
		event_dict["layer"] = layer
	if request_id:
		event_dict["request_id"] = request_id

	return event_dict


def reorder_keys_processor(
	logger: AbstractLogger,
	method_name: str,
	event_dict: dict[str, Any],
) -> dict[str, Any]:
	"""Ставит method/path в начало JSON-лога."""
	ordered_dict: dict[str, Any] = {}

	if "method" in event_dict:
		ordered_dict["method"] = event_dict.pop("method")
	if "path" in event_dict:
		ordered_dict["path"] = event_dict.pop("path")
	if "request_id" in event_dict:
		ordered_dict["request_id"] = event_dict.pop("request_id")

	ordered_dict.update(event_dict)
	return ordered_dict


def configure_logger() -> None:
	log_level = cfg.logging.level.upper()
	allowed_levels = {
		"DEBUG": 10,
		"INFO": 20,
		"WARNING": 30,
		"ERROR": 40,
		"CRITICAL": 50,
	}
	log_level = allowed_levels.get(log_level, 20)
	structlog.configure_once(
		processors=cast(Any, [
			structlog.contextvars.merge_contextvars,
			http_context_processor,
			structlog.processors.add_log_level,
			structlog.dev.set_exc_info,
			structlog.processors.TimeStamper(),
			reorder_keys_processor,
			structlog.processors.JSONRenderer(),
		]),
		context_class=dict,
		logger_factory=structlog.PrintLoggerFactory(),
		cache_logger_on_first_use=False,
		wrapper_class=structlog.make_filtering_bound_logger(log_level),
	)


class StructLogger(AbstractLogger):
	def __init__(self, context: dict[str, Any] | None = None) -> None:
		self._logger = None
		self._context = context or {}

	def _get_logger(self) -> Any:
		if self._logger is None:
			self._logger = structlog.get_logger()
		return self._logger

	def _get_caller_info(self) -> dict[str, Any]:
		import inspect

		stack = inspect.stack()
		for frame_info in stack[2:]:
			if (
				"logger.py" not in frame_info.filename
				and "structlog" not in frame_info.filename
			):
				return {
					"source_file": frame_info.filename.split("/")[-1],
					"func_name": frame_info.function,
					"lineno": frame_info.lineno,
					"pathname": frame_info.filename,
				}

		return {}

	def debug(self, message: str, **kwargs: object) -> None:
		caller_info = self._get_caller_info()
		self._get_logger().bind(**self._context, **caller_info).debug(
			message,
			**kwargs,
		)

	def info(self, message: str, **kwargs: object) -> None:
		caller_info = self._get_caller_info()
		self._get_logger().bind(**self._context, **caller_info).info(
			message,
			**kwargs,
		)

	def warning(self, message: str, **kwargs: object) -> None:
		caller_info = self._get_caller_info()
		self._get_logger().bind(**self._context, **caller_info).warning(
			message,
			**kwargs,
		)

	def error(self, message: str, **kwargs: object) -> None:
		caller_info = self._get_caller_info()
		self._get_logger().bind(**self._context, **caller_info).error(
			message,
			**kwargs,
		)

	def critical(self, message: str, **kwargs: object) -> None:
		caller_info = self._get_caller_info()
		self._get_logger().bind(**self._context, **caller_info).critical(
			message,
			**kwargs,
		)

	def bind(self, **kwargs: object) -> StructLogger:
		new_context = {**self._context, **kwargs}
		return StructLogger(new_context)


_logger_instance: AbstractLogger | None = None


def get_logger() -> AbstractLogger:
	global _logger_instance
	if _logger_instance is None:
		configure_logger()
		_logger_instance = StructLogger()
	return _logger_instance

