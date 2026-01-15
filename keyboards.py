# keyboards.py

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton


from database import Database

# ======================
# Main User Menu (Reply Keyboard)
# ======================
def main_menu_keyboard(is_admin=False):
    db = Database()
    keyboard = []
    
    if is_admin:
        keyboard.append([KeyboardButton(text="🔧 لوحة التحكم")])
    
    # Add dynamic buttons from database
    dynamic_buttons = db.get_buttons()
    temp_row = []
    for btn in dynamic_buttons:
        temp_row.append(KeyboardButton(text=btn['text']))
        if len(temp_row) == 2:  # 2 buttons per row
            keyboard.append(temp_row)
            temp_row = []
    if temp_row:
        keyboard.append(temp_row)
    
    # Default static buttons
    keyboard.append([KeyboardButton(text="ℹ️ معلومات"), KeyboardButton(text="🆘 الدعم")])
    
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        input_field_placeholder="اختر من القائمة..."
    )


# ======================
# Admin Main Menu
# ======================
def admin_main_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="👥 إدارة المشرفين",
                callback_data="admin:supervisors"
            )
        ],
        [
            InlineKeyboardButton(
                text="🧱 إدارة الأزرار",
                callback_data="admin:buttons"
            )
        ],
        [
            InlineKeyboardButton(
                text="📊 الإحصائيات",
                callback_data="admin:stats"
            )
        ]
    ])


# ======================
# Supervisors Menu
# ======================
def supervisors_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="➕ إضافة مشرف",
                callback_data="admin:add_supervisor"
            )
        ],
        [
            InlineKeyboardButton(
                text="⬅️ رجوع",
                callback_data="admin:back"
            )
        ]
    ])
