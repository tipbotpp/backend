# ruff: noqa: ANN001, ANN002, ANN202, ARG002

import traceback
from typing import Never, cast

from asyncpg.exceptions import ForeignKeyViolationError, UniqueViolationError
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse
from httpx import HTTPStatusError, RequestError
from jwt import PyJWTError
from sqlalchemy import exc
from starlette.types import ExceptionHandler

from src.services.logger import get_logger

logger = get_logger()


class ExceptionHandlers:
	def __init__(self) -> None:
		self.log = logger

	async def handle_value_error(
		self,
		request: Request,
		exc: ValueError,
	) -> JSONResponse:  # noqa: ARG002
		self.log.error(traceback.format_exc())
		return JSONResponse(
			status_code=status.HTTP_400_BAD_REQUEST,
			content={"detail": str(exc)},
		)

	async def handle_http_status_error(
		self,
		request: Request,  # noqa: ARG002
		exc: HTTPStatusError,
	) -> Never:
		self.log.error(traceback.format_exc())
		raise HTTPException(
			status_code=exc.response.status_code,
			detail=exc.response.text,
		)

	async def handle_request_error(
		self,
		request: Request,
		exc: RequestError,
	) -> Never:  # noqa: ARG002
		self.log.error(traceback.format_exc())
		raise HTTPException(
			status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
			detail="Сервис недоступен. Попробуйте позже.",
		)

	async def handle_argument_error(
		self,
		request: Request,  # noqa: ARG002
		exc: exc.ArgumentError,
	) -> JSONResponse:
		self.log.error(traceback.format_exc())
		return JSONResponse(
			status_code=status.HTTP_400_BAD_REQUEST,
			content={"detail": f"Ошибка аргумента: {exc}"},
		)

	async def handle_unique_violation_error(
		self,
		request: Request,  # noqa: ARG002
		exc: UniqueViolationError,  # noqa: ARG002
	) -> JSONResponse:
		self.log.error(traceback.format_exc())
		return JSONResponse(
			status_code=status.HTTP_409_CONFLICT,
			content={"detail": "Запись уже существует."},
		)

	async def handle_integrity_error(
		self,
		request: Request,  # noqa: ARG002
		exc: exc.IntegrityError,
	) -> JSONResponse:
		self.log.error(traceback.format_exc())
		code = exc.orig.pgcode
		if code == UniqueViolationError.sqlstate:
			return JSONResponse(
				status_code=status.HTTP_409_CONFLICT,
				content={"detail": "Запись уже существует."},
			)
		elif code == ForeignKeyViolationError.sqlstate:
			return JSONResponse(
				status_code=status.HTTP_404_NOT_FOUND,
				content={"detail": "Запись не найдена."},
			)
		else:
			return JSONResponse(
				status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
				content={"detail": "Внутренняя ошибка сервера."},
			)

	async def handle_jwt_error(
		self,
		request: Request,
		exc: PyJWTError,
	) -> JSONResponse:  # noqa: ARG002
		self.log.error(traceback.format_exc())
		return JSONResponse(
			status_code=status.HTTP_401_UNAUTHORIZED,
			content={"detail": str(exc)},
		)

	async def handle_generic_exception(
		self,
		request: Request,
		exc: Exception,
	) -> JSONResponse:  # noqa: ARG002
		self.log.error(traceback.format_exc())
		return JSONResponse(
			status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
			content={"detail": "Внутренняя ошибка сервера."},
		)

	@classmethod
	def register(cls, app: FastAPI) -> None:
		handler = cls()
		app.add_exception_handler(ValueError, cast(ExceptionHandler, handler.handle_value_error))
		app.add_exception_handler(
			HTTPStatusError,
			cast(ExceptionHandler, handler.handle_http_status_error),
		)
		app.add_exception_handler(RequestError, cast(ExceptionHandler, handler.handle_request_error))
		app.add_exception_handler(
			exc.ArgumentError,
			cast(ExceptionHandler, handler.handle_argument_error),
		)
		app.add_exception_handler(
			UniqueViolationError,
			cast(ExceptionHandler, handler.handle_unique_violation_error),
		)
		app.add_exception_handler(
			exc.IntegrityError,
			cast(ExceptionHandler, handler.handle_integrity_error),
		)
		app.add_exception_handler(PyJWTError, cast(ExceptionHandler, handler.handle_jwt_error))
		app.add_exception_handler(Exception, cast(ExceptionHandler, handler.handle_generic_exception))
