# admin_interface.py

from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, Message
from aiogram.fsm.context import FSMContext

from database import Database
from states import AddSupervisor, ManageButtons, SupportState

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
def admin_main_keyboard_markup(user_id):
    is_super = is_super_admin_user(user_id)
    buttons = []
    if is_super or db.has_permission(user_id, 'managers'):
        buttons.append([InlineKeyboardButton(text="👥 إدارة المشرفين", callback_data="admin:managers")])
    if is_super or db.has_permission(user_id, 'buttons'):
        buttons.append([InlineKeyboardButton(text="🧱 إدارة الأزرار", callback_data="admin:buttons_list")])
    if is_super or db.has_permission(user_id, 'stats'):
        buttons.append([InlineKeyboardButton(text="📊 الإحصائيات", callback_data="admin:stats")])
    if is_super or db.has_permission(user_id, 'logs'):
        buttons.append([InlineKeyboardButton(text="📜 سجل المراسلات", callback_data="admin:logs")])
    if is_super:
        buttons.append([InlineKeyboardButton(text="📢 إذاعة رسالة للكل", callback_data="admin:broadcast")])
        buttons.append([InlineKeyboardButton(text="🛡️ سجل المشرفين", callback_data="admin:admin_logs")])
    buttons.append([InlineKeyboardButton(text="⬅️ إغلاق", callback_data="admin:close")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

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

    # Clear current message and show fresh panel to ensure all buttons are loaded
    try:
        await callback.message.edit_text(
            "🔧 لوحة التحكم",
            reply_markup=admin_main_keyboard_markup(callback.from_user.id)
        )
    except Exception:
        # In case edit fails (e.g. message text is same), try sending fresh message
        await callback.message.answer(
            "🔧 لوحة التحكم",
            reply_markup=admin_main_keyboard_markup(callback.from_user.id)
        )
    await callback.answer()

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
        
        # Fresh view instead of modifying frozen callback.data
        buttons = db.get_buttons(parent_id)
        keyboard = []
        
        parent_text = ""
        if parent_id:
            parent_btn = db.get_button_by_id(parent_id)
            if parent_btn:
                parent_text = f" (داخل: {parent_btn['text']})"
                back_id = parent_btn['parent_id']
                keyboard.append([InlineKeyboardButton(text="⬅️ مستوى للأعلى", callback_data=f"admin:buttons_list:{back_id}" if back_id else "admin:buttons_list")])

        for btn_item in buttons:
            keyboard.append([
                InlineKeyboardButton(text=f"📝 {btn_item['text']}", callback_data=f"btn_edit:{btn_item['id']}"),
                InlineKeyboardButton(text="🔼", callback_data=f"btn_move:up:{btn_item['id']}"),
                InlineKeyboardButton(text="🔽", callback_data=f"btn_move:down:{btn_item['id']}"),
                InlineKeyboardButton(text="❌", callback_data=f"btn_del:{btn_item['id']}")
            ])
        
        keyboard.append([InlineKeyboardButton(text="➕ إضافة زر هنا", callback_data=f"button:add:{parent_id}" if parent_id else "button:add")])
        if not parent_id:
            keyboard.append([InlineKeyboardButton(text="⬅️ القائمة الرئيسية", callback_data="admin:panel")])
        
        await callback.message.edit_text(
            f"🧱 إدارة الأزرار{parent_text}:\n\n🔼/🔽: للترتيب.\n📝: للتعديل والدخول للأزرار الفرعية.\n❌: للحذف.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
        )
    else:
        await callback.answer("لا يمكن التحريك أكثر من ذلك", show_alert=False)

@router.callback_query(F.data == "admin:stats")
async def stats_handler_view(callback: CallbackQuery):
    total_users = db.get_total_users_count()
    
    stats_text = (
        "📊 **إحصائيات البوت الحية**\n\n"
        f"👥 إجمالي المستخدمين: `{total_users}`\n"
        "━━━━━━━━━━━━━━━\n"
        "💡 هذه الإحصائيات محدثة بشكل حي من قاعدة البيانات."
    )
    
    await callback.message.edit_text(
        stats_text,
        reply_markup=back_to_admin_button(),
        parse_mode="Markdown"
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
        [InlineKeyboardButton(text="📝 محتوى (نص، روابط، وسائط)", callback_data="type:content")],
        [InlineKeyboardButton(text="📁 زر أب (مجلد)", callback_data="type:folder")],
        [InlineKeyboardButton(text="💬 تواصل (Contact)", callback_data="type:contact")],
        [InlineKeyboardButton(text="⬅️ رجوع", callback_data="admin:panel")]
    ])
    await state.set_state(ManageButtons.waiting_for_type)
    await message.answer("اختر نوع الزر:", reply_markup=keyboard)

@router.callback_query(ManageButtons.waiting_for_type)
async def add_button_type_handler(callback: CallbackQuery, state: FSMContext):
    btn_type = callback.data.split(":")[-1]
    await state.update_data(type=btn_type)
    
    if btn_type == "contact":
        data = await state.get_data()
        db.add_button(
            text=data['text'],
            btn_type="contact",
            content="Support System",
            parent_id=data.get('parent_id'),
            created_by=callback.from_user.id
        )
        db.add_admin_log(callback.from_user.id, callback.from_user.full_name, "إضافة زر", "إدارة الأزرار", f"إضافة زر تواصل جديد: {data['text']}")
        await state.clear()
        await callback.message.edit_text("✅ تم إضافة زر التواصل بنجاح!", reply_markup=admin_main_keyboard_markup(callback.from_user.id))
        return

    if btn_type == "folder":
        data = await state.get_data()
        db.add_button(
            text=data['text'],
            btn_type="folder",
            content="Folder",
            parent_id=data.get('parent_id'),
            created_by=callback.from_user.id
        )
        db.add_admin_log(callback.from_user.id, callback.from_user.full_name, "إضافة زر", "إدارة الأزرار", f"إضافة زر مجلد جديد: {data['text']}")
        await state.clear()
        await callback.message.edit_text("✅ تم إضافة زر الأب (المجلد) بنجاح!", reply_markup=admin_main_keyboard_markup(callback.from_user.id))
        return

    await state.set_state(ManageButtons.waiting_for_content)
    await callback.message.edit_text("أرسل المحتوى الذي سيظهر عند الضغط على الزر (نص أو روابط):", reply_markup=back_to_admin_button())

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
    db.add_admin_log(message.from_user.id, message.from_user.full_name, "إضافة زر", "إدارة الأزرار", f"إضافة زر جديد: {data['text']}")
    await state.clear()
    await message.answer("✅ تم إضافة الزر بنجاح!", reply_markup=admin_main_keyboard_markup(message.from_user.id))

@router.callback_query(F.data.startswith("btn_del:"))
async def delete_button_handler_view(callback: CallbackQuery):
    btn_id = int(callback.data.split(":")[-1])
    btn = db.get_button_by_id(btn_id)
    parent_id = btn['parent_id'] if btn else None
    
    if btn:
        db.delete_button(btn_id)
        db.add_admin_log(callback.from_user.id, callback.from_user.full_name, "حذف زر", "إدارة الأزرار", f"حذف الزر: {btn['text']}")
    
    await callback.answer("✅ تم حذف الزر")
    
    # Refresh view by calling list_buttons_admin_view with a "mock" callback
    # Create a simple class to mimic the callback with new data
    class MockCallback:
        def __init__(self, original_callback, new_data):
            self.message = original_callback.message
            self.from_user = original_callback.from_user
            self.data = new_data
            self.answer = original_callback.answer
            
    mock_cb = MockCallback(callback, f"admin:buttons_list:{parent_id}" if parent_id else "admin:buttons_list")
    await list_buttons_admin_view(mock_cb)

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
    await message.answer(f"✅ تم تغيير اسم الزر إلى: {new_text}", reply_markup=admin_main_keyboard_markup(message.from_user.id))

@router.message(ManageButtons.waiting_for_new_content)
async def process_new_content(message: Message, state: FSMContext):
    data = await state.get_data()
    btn_id = data.get("edit_btn_id")
    new_content = message.text.strip()
    
    db.update_button(btn_id, content=new_content)
    await state.clear()
    await message.answer("✅ تم تحديث محتوى الزر بنجاح!", reply_markup=admin_main_keyboard_markup(message.from_user.id))

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
        reply_markup=admin_main_keyboard_markup(message.from_user.id)
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

@router.callback_query(F.data.startswith("manager:perms:"))
async def edit_manager_perms(callback: CallbackQuery):
    parts = callback.data.split(":")
    target_id = int(parts[2])
    
    if not is_super_admin_user(callback.from_user.id):
        await callback.answer("عذراً، هذا الإجراء متاح للأدمن الأساسي فقط.", show_alert=True)
        return

    # Toggle if action is specified
    if len(parts) > 3:
        feature_id = parts[3]
        current_perms = db.get_supervisor_permissions(target_id)
        granted = feature_id not in current_perms
        db.set_supervisor_permission(target_id, feature_id, granted)
        
        # Log action
        action_text = "تفعيل" if granted else "تعطيل"
        db.add_admin_log(callback.from_user.id, callback.from_user.full_name, f"{action_text} صلاحية {feature_id}", "إدارة المشرفين", f"للمشرف {target_id}")

    features = db.get_features()
    user_perms = db.get_supervisor_permissions(target_id)
    
    keyboard = []
    for f in features:
        status = "✅" if f['id'] in user_perms else "❌"
        keyboard.append([InlineKeyboardButton(text=f"{status} {f['name_ar']}", callback_data=f"manager:perms:{target_id}:{f['id']}")])
    
    keyboard.append([InlineKeyboardButton(text="⬅️ رجوع", callback_data=f"manager:view:{target_id}")])
    
    await callback.message.edit_text(
        f"⚙️ **تعديل صلاحيات المشرف: {target_id}**\nاضغط على الصلاحية للتفعيل أو التعطيل:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
        parse_mode="Markdown"
    )

@router.callback_query(F.data.startswith("manager:delete:"))
async def delete_manager_handler(callback: CallbackQuery):
    if not is_super_admin_user(callback.from_user.id):
        await callback.answer("للأدمن الأساسي فقط", show_alert=True)
        return
    
    target_id = int(callback.data.split(":")[-1])
    db.delete_supervisor(target_id)
    db.add_admin_log(callback.from_user.id, callback.from_user.full_name, "حذف مشرف", "إدارة المشرفين", f"حذف المشرف {target_id} نهائياً")
    await callback.answer("✅ تم حذف المشرف نهائياً")
    await list_managers_view(callback)

def manager_control_keyboard_markup(telegram_id: int, is_active: int, is_super: bool):
    buttons = []
    if is_active:
        buttons.append([InlineKeyboardButton(text="⛔ تعطيل المؤقت", callback_data=f"manager:disable:{telegram_id}")])
    else:
        buttons.append([InlineKeyboardButton(text="✅ تفعيل", callback_data=f"manager:enable:{telegram_id}")])
    
    if is_super:
        buttons.append([InlineKeyboardButton(text="⚙️ تعديل الصلاحيات", callback_data=f"manager:perms:{telegram_id}")])
        buttons.append([InlineKeyboardButton(text="🗑️ حذف نهائي", callback_data=f"manager:delete:{telegram_id}")])
        
    buttons.append([InlineKeyboardButton(text="⬅️ رجوع", callback_data="manager:list")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

@router.callback_query(F.data.startswith("manager:view:"))
async def manager_view_handler(callback: CallbackQuery):
    telegram_id = int(callback.data.split(":")[-1])
    user = db.get_user_by_telegram_id(telegram_id)
    is_super = is_super_admin_user(callback.from_user.id)
    await callback.message.edit_text(
        f"👤 المشرف: {telegram_id}\nالحالة: {'مفعل' if user['is_active'] else 'معطل'}\nالرتبة: {user['role']}",
        reply_markup=manager_control_keyboard_markup(telegram_id, user["is_active"], is_super)
    )

@router.callback_query(F.data.startswith("manager:disable:"))
async def disable_manager_handler(callback: CallbackQuery):
    telegram_id = int(callback.data.split(":")[-1])
    db.set_user_active(telegram_id, 0)
    await callback.answer("تم التعطيل")
    await manager_view_handler(callback)

# ======================
# Support Reply Handlers
# ======================
@router.callback_query(F.data.startswith("support:reply:"))
async def support_reply_start(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split(":")
    user_id = int(parts[2])
    button_id = int(parts[3]) if len(parts) > 3 else None
    
    await state.update_data(reply_to_user_id=user_id, reply_button_id=button_id)
    await state.set_state(SupportState.waiting_for_reply)
    await callback.message.answer(f"أرسل ردك للمستخدم ({user_id}):", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="إلغاء", callback_data="admin:panel")]]))
    await callback.answer()

@router.message(SupportState.waiting_for_reply)
async def support_reply_process(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    user_id = data.get("reply_to_user_id")
    button_id = data.get("reply_button_id")
    admin_name = message.from_user.full_name
    
    try:
        await bot.send_message(user_id, f"✉️ **رد من الإدارة:**\n\n{message.text}", parse_mode="Markdown")
        db.add_support_message(user_id, message.text, is_from_admin=1, admin_id=message.from_user.id, button_id=button_id, admin_name=admin_name)
        db.add_admin_log(message.from_user.id, admin_name, "الرد على مستخدم", "سجل المراسلات", f"رد على المستخدم {user_id}")
        await message.answer("✅ تم إرسال الرد بنجاح.")
    except Exception as e:
        await message.answer(f"❌ فشل إرسال الرد: {e}")
    
    await state.clear()

# ======================
# Logs Handlers
# ======================
@router.callback_query(F.data == "admin:logs")
async def show_logs_categories(callback: CallbackQuery):
    contact_buttons = db.get_contact_buttons()
    if not contact_buttons:
        await callback.message.edit_text("❌ لا توجد أزرار تواصل مبرمجة حالياً.", reply_markup=back_to_admin_button())
        return

    keyboard = []
    for btn in contact_buttons:
        keyboard.append([InlineKeyboardButton(text=f"📂 {btn['text']}", callback_data=f"logs:view:{btn['id']}")])
    
    keyboard.append([InlineKeyboardButton(text="⬅️ رجوع", callback_data="admin:panel")])
    
    await callback.message.edit_text("📜 اختر القسم لعرض سجل المراسلات:", reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))

@router.callback_query(F.data.startswith("logs:view:"))
async def view_section_logs(callback: CallbackQuery):
    parts = callback.data.split(":")
    button_id = int(parts[2])
    
    messages = db.get_messages_by_button(button_id)
    btn = db.get_button_by_id(button_id)
    
    if not messages:
        await callback.message.edit_text(
            f"📜 سجل المراسلات لـ {btn['text'] if btn else 'غير معروف'}:\n\nلا توجد رسائل في هذا القسم حالياً.",
            reply_markup=back_to_admin_button()
        )
        return

    logs_text = f"📜 <b>سجل المراسلات: {html.escape(btn['text'])}</b>\n\n"
    keyboard = []
    
    for msg in messages:
        sender = "🛠️ الإدارة"
        if not msg['is_from_admin']:
            username_str = f" (@{msg['username']})" if msg['username'] else ""
            sender = f"👤 {msg['full_name']}{username_str}"
        
        # Use HTML escaping for better stability
        import html
        safe_msg = html.escape(msg['message_text'])
        
        logs_text += f"<b>{html.escape(sender)}:</b>\n{safe_msg}\n"
        logs_text += f"📅 <code>{msg['timestamp']}</code>\n"
        logs_text += f"❌ /del\_{msg['id']}\n"
        logs_text += "────────────────\n"
    
    # Add clear all button
    keyboard.append([InlineKeyboardButton(text="🗑️ مسح الكل", callback_data=f"logs:clear_all:{button_id}")])
    
    # Add reply button for the last user if the last message was from a user
    last_msg = messages[-1]
    if not last_msg['is_from_admin']:
        keyboard.append([InlineKeyboardButton(text="💬 رد على آخر رسالة", callback_data=f"support:reply:{last_msg['user_id']}:{button_id}")])
    
    keyboard.append([InlineKeyboardButton(text="⬅️ رجوع", callback_data="admin:logs")])
    
    # Limit message length
    if len(logs_text) > 4000:
        logs_text = logs_text[-4000:]
        
    await callback.message.edit_text(logs_text, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard), parse_mode="HTML")

@router.callback_query(F.data.startswith("logs:clear_all:"))
async def clear_all_logs(callback: CallbackQuery):
    button_id = int(callback.data.split(":")[-1])
    db.clear_support_messages_by_button(button_id)
    await callback.answer("✅ تم مسح جميع الرسائل بنجاح")
    await callback.message.edit_text("📜 تم مسح السجل بالكامل.", reply_markup=back_to_admin_button())

@router.message(F.text.startswith("/del_log_"))
async def delete_single_admin_log_handler(message: Message):
    if not is_super_admin_user(message.from_user.id):
        return
    
    try:
        parts = message.text.split("_")
        msg_id = int(parts[-1])
        db.delete_admin_log(msg_id)
        await message.answer("✅ تم حذف السجل بنجاح.")
    except Exception:
        await message.answer("❌ أمر غير صالح.")

@router.message(F.text.startswith("/del_"))
async def delete_single_log_command(message: Message):
    if not is_admin_user(message.from_user.id):
        return
    
    if message.text.startswith("/del_log_"):
        return

    try:
        parts = message.text.split("_")
        msg_id = int(parts[-1])
        msg = db.get_message_by_id(msg_id)
        if msg:
            db.delete_support_message(msg_id)
            await message.answer("✅ تم حذف الرسالة بنجاح.")
        else:
            await message.answer("❌ الرسالة غير موجودة.")
    except Exception:
        await message.answer("❌ أمر غير صالح.")

# ======================
# Broadcast Handlers
# ======================
@router.callback_query(F.data == "admin:broadcast")
async def broadcast_start_handler(callback: CallbackQuery, state: FSMContext):
    if not is_super_admin_user(callback.from_user.id):
        await callback.answer("للأدمن الأساسي فقط", show_alert=True)
        return
    
    from states import BroadcastState
    await state.set_state(BroadcastState.waiting_for_message)
    await callback.message.edit_text(
        "📢 **قسم الإذاعة العامة**\n\nأرسل الرسالة التي تريد توجيهها لجميع مستخدمي البوت:",
        reply_markup=back_to_admin_button(),
        parse_mode="Markdown"
    )

@router.message(F.text, F.state == "BroadcastState:waiting_for_message")
async def broadcast_process_handler(message: Message, state: FSMContext, bot: Bot):
    from states import BroadcastState
    current_state = await state.get_state()
    if current_state != BroadcastState.waiting_for_message.state:
        return

    broadcast_text = message.text
    await state.clear()
    
    # Get all users from DB
    db.cursor.execute("SELECT telegram_id FROM users WHERE role = 'user'")
    users = db.cursor.fetchall()
    
    if not users:
        await message.answer("❌ لا يوجد مستخدمون لإرسال الرسالة إليهم.")
        return

    status_msg = await message.answer(f"⏳ جاري بدء الإذاعة لـ {len(users)} مستخدم...")
    
    success_count = 0
    fail_count = 0
    
    for user in users:
        try:
            await bot.send_message(user['telegram_id'], f"📢 **إعلان من الإدارة:**\n\n{broadcast_text}", parse_mode="Markdown")
            success_count += 1
        except Exception:
            fail_count += 1
            
    db.add_admin_log(message.from_user.id, message.from_user.full_name, "إذاعة عامة", "النظام", f"تم الإرسال لـ {success_count} مستخدم (فشل {fail_count})")
    
    await status_msg.edit_text(
        f"✅ **اكتملت عملية الإذاعة**\n\n"
        f"🔹 تم الإرسال بنجاح: `{success_count}`\n"
        f"🔸 فشل الإرسال (بوت محظور): `{fail_count}`",
        reply_markup=admin_main_keyboard_markup(message.from_user.id),
        parse_mode="Markdown"
    )
