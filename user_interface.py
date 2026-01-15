# user_interface.py

from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from database import Database

from states import ManageButtons
from aiogram.fsm.context import FSMContext

router = Router()
db = Database()

@router.message()
async def dynamic_button_handler(message: Message, state: FSMContext):
    if not message.text:
        return

    # Check for active state (don't interfere with admin input)
    current_state = await state.get_state()
    if current_state:
        return

    # Check if the text matches any dynamic button
    buttons = db.get_buttons()
    for btn in buttons:
        if message.text.strip() == btn['text'].strip():
            if btn['type'] == 'text':
                await message.answer(btn['content'])
            elif btn['type'] == 'url':
                url = btn['content'].strip()
                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🔗 فتح الرابط", url=url)]
                ])
                await message.answer(f"إليك الرابط الخاص بـ {btn['text']}:", reply_markup=keyboard)
            elif btn['type'] == 'contact':
                # Logic: Allow the user to send a message that admins/supervisors will receive
                await message.answer(
                    f"📧 خدمة تواصل مع الإدارة:\n\nأرسل رسالتك الآن وسيقوم المشرفون بالرد عليك قريباً."
                )
                # Here we could set a state like "waiting_for_user_contact_message" 
                # but for simplicity, let's assume they just type it.
            return

    # If no dynamic button matches, we could handle other generic logic here
    pass
