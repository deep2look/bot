from aiogram.fsm.state import StatesGroup, State

class AddSupervisor(StatesGroup):
    waiting_for_username = State()

