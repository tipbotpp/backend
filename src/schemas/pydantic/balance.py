from __future__ import annotations

from pydantic import Field

from src.schemas.pydantic.common import BaseSchema


class BalanceResponse(BaseSchema):
	balance: int = Field(description="Текущий баланс пользователя в монетах")
	currency: str = Field(default="coins", description="Валюта (всегда coins)")


class TopupBody(BaseSchema):
	amount: int = Field(
		gt=0,
		le=100_000,
		description="Количество монет для пополнения баланса",
	)


class TopupResponse(BaseSchema):
	previous_balance: int = Field(description="Баланс до пополнения")
	added_amount: int = Field(description="Зачисленное количество монет")
	new_balance: int = Field(description="Новый баланс после пополнения")
