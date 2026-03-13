from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class BalanceTransactionCreateDTO:
	user_id: int
	amount: int
	type: str
	ref_donation_id: int | None = None


@dataclass(slots=True)
class BalanceTransactionDTO:
	id: int
	user_id: int
	amount: int
	type: str
	ref_donation_id: int | None
	created_at: datetime
