from aiogram.fsm.state import StatesGroup, State

class AddSupervisor(StatesGroup):
    waiting_for_username = State()

class ManageButtons(StatesGroup):
    waiting_for_text = State()
    waiting_for_type = State()
    waiting_for_content = State()
    
    waiting_for_new_text = State()
    waiting_for_new_content = State()

class SupportState(StatesGroup):
    waiting_for_message = State()
    waiting_for_reply = State()

class BroadcastState(StatesGroup):
    waiting_for_message = State()

