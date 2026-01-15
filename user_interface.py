# user_interface.py

from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from database import Database
from aiogram.fsm.context import FSMContext

router = Router()
db = Database()

def get_user_keyboard(parent_id=None):
    buttons = db.get_buttons(parent_id)
    kb_buttons = []
    row = []
    for btn in buttons:
        row.append(KeyboardButton(text=btn['text']))
        if len(row) == 2:
            kb_buttons.append(row)
            row = []
    if row:
        kb_buttons.append(row)
    
    if parent_id:
        kb_buttons.append([KeyboardButton(text="⬅️ العودة للقائمة السابقة")])
        kb_buttons.append([KeyboardButton(text="🏠 القائمة الرئيسية")])
        
    return ReplyKeyboardMarkup(keyboard=kb_buttons, resize_keyboard=True)

@router.message(F.text == "🏠 القائمة الرئيسية")
async def main_menu_handler(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("🏠 القائمة الرئيسية", reply_markup=get_user_keyboard())

@router.message(F.text == "⬅️ العودة للقائمة السابقة")
async def back_menu_handler(message: Message, state: FSMContext):
    data = await state.get_data()
    current_parent_id = data.get("current_parent_id")
    
    if not current_parent_id:
        await message.answer("أنت في القائمة الرئيسية", reply_markup=get_user_keyboard())
        return

    current_btn = db.get_button_by_id(current_parent_id)
    grandparent_id = current_btn['parent_id'] if current_btn else None
    
    await state.update_data(current_parent_id=grandparent_id)
    await message.answer("العودة للخلف...", reply_markup=get_user_keyboard(grandparent_id))

@router.message()
async def dynamic_button_handler(message: Message, state: FSMContext):
    if not message.text:
        return

    # Check for active admin state
    current_state = await state.get_state()
    if current_state:
        return

    data = await state.get_data()
    current_parent_id = data.get("current_parent_id")
    
    # Check if the text matches any dynamic button in the current level
    buttons = db.get_buttons(current_parent_id)
    target_btn = None
    for btn in buttons:
        if message.text.strip() == btn['text'].strip():
            target_btn = btn
            break
    
    if not target_btn:
        return

    # Check if it has sub-buttons (act as a folder/menu)
    sub_buttons = db.get_buttons(target_btn['id'])
    
    if sub_buttons:
        await state.update_data(current_parent_id=target_btn['id'])
        await message.answer(f"📂 {target_btn['text']}", reply_markup=get_user_keyboard(target_btn['id']))
        return

    # Normal button actions
    if target_btn['type'] == 'text':
        await message.answer(target_btn['content'])
    elif target_btn['type'] == 'url':
        url = target_btn['content'].strip()
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔗 فتح الرابط", url=url)]
        ])
        await message.answer(f"إليك الرابط الخاص بـ {target_btn['text']}:", reply_markup=keyboard)
    elif target_btn['type'] == 'contact':
        await message.answer(
            f"📞 تواصل مع الإدارة بخصوص: {target_btn['text']}\n\n{target_btn['content']}"
        )
