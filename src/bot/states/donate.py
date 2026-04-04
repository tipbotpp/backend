from aiogram.fsm.state import State, StatesGroup


class DonateStates(StatesGroup):
	waiting_streamer_id = State()
	waiting_amount = State()
	waiting_message = State()
