from typing import Any

from fastapi import HTTPException


class BaseHTTPException(HTTPException):
	status_code: int
	detail: str
	headers: dict[str, str] | None = None

	def __init__(self, *args: Any, **kwargs: Any) -> None:
		super().__init__(
			status_code=self.status_code,
			detail=self.detail,
			headers=dict(self.headers) if self.headers else None,
		)
