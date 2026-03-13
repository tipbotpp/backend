from __future__ import annotations

from src.schemas.pydantic.common import BaseSchema


class BalanceResponse(BaseSchema):
	balance: int
	currency: str = "coins"


class TopupBody(BaseSchema):
	amount: int


class TopupResponse(BaseSchema):
	previous_balance: int
	added_amount: int
	new_balance: int
