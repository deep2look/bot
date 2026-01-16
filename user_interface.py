# user_interface.py

from aiogram import Router, F, Bot
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from database import Database
from aiogram.fsm.context import FSMContext

router = Router()
db = Database()

def get_user_keyboard(parent_id=None):
    buttons = db.get_buttons(parent_id)
    kb_buttons = []
    
    # Always add the refresh button at the top
    kb_buttons.append([KeyboardButton(text="🔄 تحديث البوت")])
    
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

from states import SupportState

# ... existing code ...

@router.message(SupportState.waiting_for_message)
async def user_submit_support(message: Message, state: FSMContext, bot: Bot):
    if message.text == "🔄 تحديث البوت" or message.text == "🏠 القائمة الرئيسية":
        await state.clear()
        return

    data = await state.get_data()
    button_id = data.get("contact_button_id")

    # Save to DB
    db.add_support_message(message.from_user.id, message.text, button_id=button_id)
    
    # Notify Admins
    admins = db.get_admins()
    # Also include super admin
    from config import SUPER_ADMIN_ID
    admin_ids = [admin['telegram_id'] for admin in admins]
    if SUPER_ADMIN_ID not in admin_ids:
        admin_ids.append(SUPER_ADMIN_ID)
        
    for admin_id in admin_ids:
        try:
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="💬 رد على المستخدم", callback_data=f"support:reply:{message.from_user.id}:{button_id}")]
            ])
            await bot.send_message(
                admin_id, 
                f"📥 **رسالة دعم جديدة**\nمن: {message.from_user.full_name} ({message.from_user.id})\nالقسم: {data.get('contact_button_text', 'غير محدد')}\n\nالرسالة:\n{message.text}",
                reply_markup=kb,
                parse_mode="Markdown"
            )
        except Exception:
            pass

    await message.answer("✅ تم إرسال رسالتك للإدارة. سيتم الرد عليك في أقرب وقت ممكن.")
    await state.clear()

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
    if target_btn['type'] == 'folder':
        await state.update_data(current_parent_id=target_btn['id'])
        await message.answer(f"📂 {target_btn['text']}", reply_markup=get_user_keyboard(target_btn['id']))
        return
        
    if target_btn['type'] == 'contact':
        await state.set_state(SupportState.waiting_for_message)
        await state.update_data(contact_button_id=target_btn['id'], contact_button_text=target_btn['text'])
        await message.answer(
            f"🚀 أنت الآن في وضع التواصل المباشر مع الإدارة بخصوص: {target_btn['text']}\n\nأرسل رسالتك الآن وسيقوم أحد المشرفين بالرد عليك هنا.",
            reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="🏠 القائمة الرئيسية")]], resize_keyboard=True)
        )
    else:
        # For 'content', 'text', 'url', etc. - just send the content
        await message.answer(target_btn['content'])
