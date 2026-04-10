from __future__ import annotations

from pydantic import Field

from src.schemas.pydantic.common import BaseSchema


class BalanceResponse(BaseSchema):
	balance: int
	currency: str = "coins"


class TopupBody(BaseSchema):
	amount: int = Field(gt=0, description="Количество монет для пополнения")


class TopupResponse(BaseSchema):
	previous_balance: int
	added_amount: int
	new_balance: int
