from fastapi import status

from .base import BaseHTTPException

# ── Auth ─────────────────────────────────────────────────────────────────────


class InvalidInitDataError(BaseHTTPException):
	status_code = status.HTTP_401_UNAUTHORIZED
	detail = "Невалидный initData"


class InvalidTokenError(BaseHTTPException):
	status_code = status.HTTP_401_UNAUTHORIZED
	detail = "Неверный или истёкший токен"


class TokenRevokedError(BaseHTTPException):
	status_code = status.HTTP_401_UNAUTHORIZED
	detail = "Сессия отозвана"


# ── Common ────────────────────────────────────────────────────────────────────


class UnauthorizedError(BaseHTTPException):
	status_code = status.HTTP_401_UNAUTHORIZED
	detail = "Необходима авторизация"


class ForbiddenError(BaseHTTPException):
	status_code = status.HTTP_403_FORBIDDEN
	detail = "Недостаточно прав"


class NotFoundError(BaseHTTPException):
	status_code = status.HTTP_404_NOT_FOUND
	detail = "Объект не найден"


class ConflictError(BaseHTTPException):
	status_code = status.HTTP_409_CONFLICT
	detail = "Конфликт данных"


# ── Users ─────────────────────────────────────────────────────────────────────


class UserNotFoundError(BaseHTTPException):
	status_code = status.HTTP_404_NOT_FOUND
	detail = "Пользователь не найден"


class RoleAlreadySetError(BaseHTTPException):
	status_code = status.HTTP_409_CONFLICT
	detail = "Роль уже установлена"


class InvalidRoleError(BaseHTTPException):
	status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
	detail = "Допустимые роли: viewer, streamer"


class StreamerRequiredError(BaseHTTPException):
	status_code = status.HTTP_403_FORBIDDEN
	detail = "Доступно только для стримеров"


class ViewerRequiredError(BaseHTTPException):
	status_code = status.HTTP_403_FORBIDDEN
	detail = "Доступно только для зрителей"


# ── Stream ────────────────────────────────────────────────────────────────────


class StreamAlreadyActiveError(BaseHTTPException):
	status_code = status.HTTP_409_CONFLICT
	detail = "Стрим уже запущен"


class StreamNotActiveError(BaseHTTPException):
	status_code = status.HTTP_404_NOT_FOUND
	detail = "Активный стрим не найден"


# ── Donations ─────────────────────────────────────────────────────────────────


class InsufficientBalanceError(BaseHTTPException):
	status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
	detail = "Недостаточно монет"


class DonationNotFoundError(BaseHTTPException):
	status_code = status.HTTP_404_NOT_FOUND
	detail = "Донат не найден"


class DonationRejectedToxicityError(BaseHTTPException):
	status_code = 451
	detail = "Сообщение отклонено модерацией"


class DonationRejectedStopwordError(BaseHTTPException):
	status_code = 451
	detail = "Сообщение содержит запрещённое слово стримера"
