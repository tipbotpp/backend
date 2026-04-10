from aiogram.fsm.state import State, StatesGroup


class TopupStates(StatesGroup):
	waiting_amount = State()
