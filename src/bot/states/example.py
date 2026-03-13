from aiogram.fsm.state import State, StatesGroup


class ExampleStates(StatesGroup):
	"""Пример группы состояний FSM."""

	waiting_for_input = State()
