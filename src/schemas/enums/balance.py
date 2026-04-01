from enum import StrEnum


class BalanceTransactionType(StrEnum):
	TOPUP = "topup"
	DONATION_SENT = "donation_sent"
	DONATION_RECEIVED = "donation_received"
	PASSIVE_INCOME = "passive_income"
	INITIAL = "initial"
