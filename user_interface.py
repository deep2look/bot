# user_interface.py

from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from database import Database

router = Router()
db = Database()

@router.message()  # Simplified fallback to handle all messages
async def dynamic_button_handler(message: Message):
    if not message.text:
        return

    # Check if the text matches any dynamic button
    buttons = db.get_buttons()
    for btn in buttons:
        # Normalize text to avoid matching issues (strip spaces)
        if message.text.strip() == btn['text'].strip():
            if btn['type'] == 'text':
                await message.answer(btn['content'])
            elif btn['type'] == 'url':
                # Ensure the URL is valid by stripping spaces
                url = btn['content'].strip()
                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🔗 فتح الرابط", url=url)]
                ])
                await message.answer(f"إليك الرابط الخاص بـ {btn['text']}:", reply_markup=keyboard)
            elif btn['type'] == 'contact':
                # Simplified contact handling
                await message.answer(f"📞 للتواصل بخصوص {btn['text']}:\n\n{btn['content']}")
            return

    # If no dynamic button matches, we could handle other generic logic here
    pass
