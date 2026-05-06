from aiogram.fsm.state import State, StatesGroup


class StopwordStates(StatesGroup):
	waiting_word = State()


class GoalStates(StatesGroup):
	waiting_title = State()
	waiting_amount = State()
