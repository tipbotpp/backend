from dishka.integrations.fastapi import DishkaRoute, FromDishka, inject
from fastapi import APIRouter

from src.di.deps.auth import CurrentUserDep
from src.schemas.pydantic import balance as balance_schema
from src.services.balance import BalanceService
from src.services.logger import get_logger

router = APIRouter(prefix="/balance", route_class=DishkaRoute)

logger = get_logger().bind(layer="endpoint", module="balance")


@router.get("", response_model=balance_schema.BalanceResponse)
@inject
async def get_balance(user: CurrentUserDep) -> balance_schema.BalanceResponse:
	log = logger.bind(request_user_id=user.telegram_id)
	log.debug("GET /balance", balance=user.balance)
	return balance_schema.BalanceResponse(balance=user.balance)


@router.post("/topup", response_model=balance_schema.TopupResponse)
@inject
async def topup(
	body: balance_schema.TopupBody,
	balance_service: FromDishka[BalanceService],
	user: CurrentUserDep,
) -> balance_schema.TopupResponse:
	log = logger.bind(request_user_id=user.telegram_id, request_amount=body.amount)
	log.debug("POST /balance/topup")

	previous_balance, new_balance = await balance_service.topup(user, body.amount)

	log.info("topup success", previous_balance=previous_balance, new_balance=new_balance)
	return balance_schema.TopupResponse(
		previous_balance=previous_balance,
		added_amount=body.amount,
		new_balance=new_balance,
	)
