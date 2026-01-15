# user_interface.py

from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from database import Database

router = Router()
db = Database()

@router.message(lambda message: True)  # Fallback to handle dynamic buttons or general text
async def dynamic_button_handler(message: Message):
    # Check if the text matches any dynamic button
    buttons = db.get_buttons()
    for btn in buttons:
        if message.text == btn['text']:
            if btn['type'] == 'text':
                await message.answer(btn['content'])
            elif btn['type'] == 'url':
                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🔗 فتح الرابط", url=btn['content'])]
                ])
                await message.answer(f"إليك الرابط الخاص بـ {btn['text']}:", reply_markup=keyboard)
            elif btn['type'] == 'contact':
                await message.answer(f"للتواصل بخصوص {btn['text']}:\n{btn['content']}")
            return

    # If no dynamic button matches, we could handle other generic logic here
    pass
