# admin_interface.py

from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, Message
from aiogram.fsm.context import FSMContext

from database import Database
from states import AddSupervisor, ManageButtons

router = Router()
db = Database()

# ======================
# Permissions
# ======================
def is_admin_user(telegram_id: int) -> bool:
    user = db.get_user_by_telegram_id(telegram_id)
    return bool(user and user["role"] in ("super_admin", "admin", "supervisor"))

def is_super_admin_user(telegram_id: int) -> bool:
    user = db.get_user_by_telegram_id(telegram_id)
    return bool(user and user["role"] == "super_admin")

# ======================
# Keyboards
# ======================
def admin_main_keyboard_markup():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👥 إدارة المشرفين", callback_data="admin:managers")],
        [InlineKeyboardButton(text="🧱 إدارة الأزرار", callback_data="admin:buttons_list")],
        [InlineKeyboardButton(text="📊 الإحصائيات", callback_data="admin:stats")],
        [InlineKeyboardButton(text="⬅️ إغلاق", callback_data="admin:close")]
    ])

def managers_keyboard_markup():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ إضافة مشرف", callback_data="manager:add")],
        [InlineKeyboardButton(text="📋 عرض المشرفين", callback_data="manager:list")],
        [InlineKeyboardButton(text="⬅️ رجوع", callback_data="admin:panel")],
    ])

def back_to_admin_button():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ رجوع", callback_data="admin:panel")]
    ])

# ======================
# Handlers
# ======================
@router.callback_query(F.data == "admin:panel")
@router.callback_query(F.data == "admin:back")
async def admin_panel_view(callback: CallbackQuery, state: FSMContext):
    await state.clear() # Clear state if returning from a flow
    if not is_admin_user(callback.from_user.id):
        await callback.answer("غير مصرح", show_alert=True)
        return

    # Check if message is accessible
    if callback.message:
        try:
            await callback.message.edit_text(
                "🔧 لوحة التحكم",
                reply_markup=admin_main_keyboard_markup()
            )
        except Exception:
            await callback.message.answer(
                "🔧 لوحة التحكم",
                reply_markup=admin_main_keyboard_markup()
            )
    else:
        await callback.answer("حدث خطأ في الوصول للرسالة")

@router.callback_query(F.data == "admin:close")
async def close_admin_panel(callback: CallbackQuery):
    await callback.message.delete()

@router.callback_query(F.data == "admin:managers")
@router.callback_query(F.data == "admin:supervisors")
async def managers_menu_view(callback: CallbackQuery):
    await callback.message.edit_text(
        "👥 إدارة المشرفين",
        reply_markup=managers_keyboard_markup()
    )

# ======================
# Buttons Management
# ======================
@router.callback_query(F.data == "admin:buttons")
@router.callback_query(F.data.startswith("admin:buttons_list:"))
@router.callback_query(F.data == "admin:buttons_list")
async def list_buttons_admin_view(callback: CallbackQuery):
    parent_id = None
    if callback.data.startswith("admin:buttons_list:"):
        parts = callback.data.split(":")
        if len(parts) > 2:
            try:
                parent_id = int(parts[-1])
            except ValueError:
                parent_id = None
    
    buttons = db.get_buttons(parent_id)
    keyboard = []
    
    parent_text = ""
    if parent_id:
        parent_btn = db.get_button_by_id(parent_id)
        if parent_btn:
            parent_text = f" (داخل: {parent_btn['text']})"
            back_id = parent_btn['parent_id']
            keyboard.append([InlineKeyboardButton(text="⬅️ مستوى للأعلى", callback_data=f"admin:buttons_list:{back_id}" if back_id else "admin:buttons_list")])

    for btn in buttons:
        keyboard.append([
            InlineKeyboardButton(text=f"📝 {btn['text']}", callback_data=f"btn_edit:{btn['id']}"),
            InlineKeyboardButton(text="🔼", callback_data=f"btn_move:up:{btn['id']}"),
            InlineKeyboardButton(text="🔽", callback_data=f"btn_move:down:{btn['id']}"),
            InlineKeyboardButton(text="❌", callback_data=f"btn_del:{btn['id']}")
        ])
    
    keyboard.append([InlineKeyboardButton(text="➕ إضافة زر هنا", callback_data=f"button:add:{parent_id}" if parent_id else "button:add")])
    if not parent_id:
        keyboard.append([InlineKeyboardButton(text="⬅️ القائمة الرئيسية", callback_data="admin:panel")])
    
    await callback.message.edit_text(
        f"🧱 إدارة الأزرار{parent_text}:\n\n🔼/🔽: للترتيب.\n📝: للتعديل والدخول للأزرار الفرعية.\n❌: للحذف.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )

@router.callback_query(F.data.startswith("btn_move:"))
async def move_button_handler(callback: CallbackQuery):
    parts = callback.data.split(":")
    direction = parts[1]
    btn_id = int(parts[2])
    
    if db.move_button(btn_id, direction):
        await callback.answer("تم تغيير الترتيب")
        btn = db.get_button_by_id(btn_id)
        parent_id = btn['parent_id'] if btn else None
        callback.data = f"admin:buttons_list:{parent_id}" if parent_id else "admin:buttons_list"
        await list_buttons_admin_view(callback)
    else:
        await callback.answer("لا يمكن التحريك أكثر من ذلك", show_alert=False)

@router.callback_query(F.data == "admin:stats")
async def stats_handler_view(callback: CallbackQuery):
    await callback.message.edit_text(
        "📊 إحصائيات البوت:\n\nقريباً سيتم عرض إحصائيات مفصلة هنا.",
        reply_markup=back_to_admin_button()
    )

@router.callback_query(F.data.startswith("button:add"))
async def add_button_start_handler(callback: CallbackQuery, state: FSMContext):
    parent_id = None
    parts = callback.data.split(":")
    if len(parts) > 2:
        try:
            parent_id = int(parts[2])
        except ValueError:
            parent_id = None
    
    await state.update_data(parent_id=parent_id)
    await state.set_state(ManageButtons.waiting_for_text)
    await callback.message.edit_text("أرسل نص الزر الذي سيظهر للمستخدمين:", reply_markup=back_to_admin_button())

@router.message(ManageButtons.waiting_for_text)
async def add_button_text_handler(message: Message, state: FSMContext):
    await state.update_data(text=message.text)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="نص (رسالة)", callback_data="type:text")],
        [InlineKeyboardButton(text="رابط (URL)", callback_data="type:url")],
        [InlineKeyboardButton(text="تواصل (Contact)", callback_data="type:contact")],
        [InlineKeyboardButton(text="⬅️ رجوع", callback_data="admin:panel")]
    ])
    await state.set_state(ManageButtons.waiting_for_type)
    await message.answer("اختر نوع الزر:", reply_markup=keyboard)

@router.callback_query(ManageButtons.waiting_for_type)
async def add_button_type_handler(callback: CallbackQuery, state: FSMContext):
    btn_type = callback.data.split(":")[-1]
    await state.update_data(type=btn_type)
    await state.set_state(ManageButtons.waiting_for_content)
    
    if btn_type == "text":
        await callback.message.edit_text("أرسل النص الذي سيقوم البوت بإرساله عند الضغط على الزر:", reply_markup=back_to_admin_button())
    elif btn_type == "url":
        await callback.message.edit_text("أرسل الرابط (http://...):", reply_markup=back_to_admin_button())
    elif btn_type == "contact":
        await callback.message.edit_text("أرسل المعرف أو رقم الهاتف للتواصل:", reply_markup=back_to_admin_button())

@router.message(ManageButtons.waiting_for_content)
async def add_button_finish_handler(message: Message, state: FSMContext):
    data = await state.get_data()
    db.add_button(
        text=data['text'],
        btn_type=data['type'],
        content=message.text,
        parent_id=data.get('parent_id'),
        created_by=message.from_user.id
    )
    await state.clear()
    await message.answer("✅ تم إضافة الزر بنجاح!", reply_markup=admin_main_keyboard_markup())

@router.callback_query(F.data.startswith("btn_del:"))
async def delete_button_handler_view(callback: CallbackQuery):
    btn_id = int(callback.data.split(":")[-1])
    btn = db.get_button_by_id(btn_id)
    parent_id = btn['parent_id'] if btn else None
    db.delete_button(btn_id)
    await callback.answer("✅ تم حذف الزر")
    callback.data = f"admin:buttons_list:{parent_id}" if parent_id else "admin:buttons_list"
    await list_buttons_admin_view(callback)

@router.callback_query(F.data.startswith("btn_edit:"))
async def edit_button_handler(callback: CallbackQuery, state: FSMContext):
    btn_id = int(callback.data.split(":")[-1])
    btn = db.get_button_by_id(btn_id)
    
    if not btn:
        await callback.answer("الزر غير موجود")
        return

    await state.update_data(edit_btn_id=btn_id)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📂 الأزرار الفرعية (داخل هذا الزر)", callback_data=f"admin:buttons_list:{btn_id}")],
        [InlineKeyboardButton(text="✏️ تغيير الاسم", callback_data=f"btn_edit_field:text:{btn_id}")],
        [InlineKeyboardButton(text="📝 تغيير المحتوى", callback_data=f"btn_edit_field:content:{btn_id}")],
        [InlineKeyboardButton(text="⬅️ رجوع", callback_data=f"admin:buttons_list:{btn['parent_id']}" if btn['parent_id'] else "admin:buttons_list")]
    ])
    
    await callback.message.edit_text(
        f"📝 تعديل الزر: {btn['text']}\n"
        f"النوع: {btn['type']}\n"
        f"المحتوى الحالي: {btn['content']}\n\n"
        "ماذا تريد أن تعدل؟ أو أضف أزراراً فرعية بالداخل.",
        reply_markup=keyboard
    )

@router.callback_query(F.data.startswith("btn_edit_field:"))
async def edit_button_field_handler(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split(":")
    field = parts[1]
    btn_id = int(parts[2])
    
    await state.update_data(edit_field=field, edit_btn_id=btn_id)
    
    if field == "text":
        await state.set_state(ManageButtons.waiting_for_new_text)
        await callback.message.edit_text("أرسل الاسم الجديد للزر:", reply_markup=back_to_admin_button())
    else:
        await state.set_state(ManageButtons.waiting_for_new_content)
        btn = db.get_button_by_id(btn_id)
        msg = "أرسل المحتوى الجديد للزر:"
        if btn['type'] == 'url':
            msg = "أرسل الرابط الجديد (http://...):"
        elif btn['type'] == 'contact':
            msg = "أرسل معلومات التواصل الجديدة:"
        
        await callback.message.edit_text(msg, reply_markup=back_to_admin_button())

@router.message(ManageButtons.waiting_for_new_text)
async def process_new_text(message: Message, state: FSMContext):
    data = await state.get_data()
    btn_id = data.get("edit_btn_id")
    new_text = message.text.strip()
    
    db.update_button(btn_id, text=new_text)
    await state.clear()
    await message.answer(f"✅ تم تغيير اسم الزر إلى: {new_text}", reply_markup=admin_main_keyboard_markup())

@router.message(ManageButtons.waiting_for_new_content)
async def process_new_content(message: Message, state: FSMContext):
    data = await state.get_data()
    btn_id = data.get("edit_btn_id")
    new_content = message.text.strip()
    
    db.update_button(btn_id, content=new_content)
    await state.clear()
    await message.answer("✅ تم تحديث محتوى الزر بنجاح!", reply_markup=admin_main_keyboard_markup())

# ======================
# Add Supervisor Handlers
# ======================
@router.callback_query(F.data == "manager:add")
async def add_manager_start_view(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AddSupervisor.waiting_for_username)
    await callback.message.edit_text(
        "📥 أرسل معرف المشرف (بدون @)\nمثال: username",
        reply_markup=back_to_admin_button()
    )

@router.message(AddSupervisor.waiting_for_username)
async def add_manager_finish_view(message: Message, state: FSMContext, bot: Bot):
    username = message.text.strip().lstrip("@")
    if not username.isalnum():
        await message.answer("❌ معرف غير صالح", reply_markup=back_to_admin_button())
        return
    try:
        chat = await bot.get_chat(f"@{username}")
    except Exception:
        await message.answer("❌ لم يتم العثور على مستخدم بهذا المعرف", reply_markup=back_to_admin_button())
        return
    telegram_id = chat.id
    db.add_user(telegram_id=telegram_id, role="supervisor")
    await state.clear()
    await message.answer(
        f"✅ تم إضافة المشرف @{username} بنجاح",
        reply_markup=admin_main_keyboard_markup()
    )

@router.callback_query(F.data == "manager:list")
async def list_managers_view(callback: CallbackQuery):
    admins = db.get_admins()
    if not admins:
        await callback.message.edit_text(
            "لا يوجد مشرفون حاليًا",
            reply_markup=managers_keyboard_markup()
        )
        return
    keyboard = []
    for admin in admins:
        keyboard.append([
            InlineKeyboardButton(
                text=f"👤 {admin['telegram_id']}",
                callback_data=f"manager:view:{admin['telegram_id']}"
            )
        ])
    keyboard.append(
        [InlineKeyboardButton(text="⬅️ رجوع", callback_data="admin:managers")]
    )
    await callback.message.edit_text(
        "📋 قائمة المشرفين:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )

def manager_control_keyboard_markup(telegram_id: int, is_active: int):
    buttons = []
    if is_active:
        buttons.append(InlineKeyboardButton(text="⛔ تعطيل", callback_data=f"manager:disable:{telegram_id}"))
    else:
        buttons.append(InlineKeyboardButton(text="✅ تفعيل", callback_data=f"manager:enable:{telegram_id}"))
    return InlineKeyboardMarkup(inline_keyboard=[buttons, [InlineKeyboardButton(text="⬅️ رجوع", callback_data="manager:list")]])

@router.callback_query(F.data.startswith("manager:view:"))
async def manager_view_handler(callback: CallbackQuery):
    telegram_id = int(callback.data.split(":")[-1])
    user = db.get_user_by_telegram_id(telegram_id)
    await callback.message.edit_text(
        f"👤 المشرف: {telegram_id}\nالحالة: {'مفعل' if user['is_active'] else 'معطل'}",
        reply_markup=manager_control_keyboard_markup(telegram_id, user["is_active"])
    )

@router.callback_query(F.data.startswith("manager:disable:"))
async def disable_manager_handler(callback: CallbackQuery):
    telegram_id = int(callback.data.split(":")[-1])
    db.set_user_active(telegram_id, 0)
    await callback.answer("تم التعطيل")
    await manager_view_handler(callback)

@router.callback_query(F.data.startswith("manager:enable:"))
async def enable_manager_handler(callback: CallbackQuery):
    telegram_id = int(callback.data.split(":")[-1])
    db.set_user_active(telegram_id, 1)
    await callback.answer("تم التفعيل")
    await manager_view_handler(callback)
