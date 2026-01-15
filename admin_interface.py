# admin_interface.py

from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, Message
from aiogram.fsm.context import FSMContext

from database import Database
from states import AddSupervisor
from aiogram import Bot


router = Router()
db = Database()


# ======================
# Permissions
# ======================
def is_super_admin(telegram_id: int) -> bool:
    user = db.get_user_by_telegram_id(telegram_id)
    return bool(user and user["role"] == "super_admin")


# ======================
# Keyboards
# ======================
def admin_main_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👥 إدارة المشرفين", callback_data="admin:managers")],
        [InlineKeyboardButton(text="🧱 إدارة الأزرار", callback_data="admin:buttons")],
    ])


def managers_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ إضافة مشرف", callback_data="manager:add")],
        [InlineKeyboardButton(text="📋 عرض المشرفين", callback_data="manager:list")],
        [InlineKeyboardButton(text="⬅️ رجوع", callback_data="admin:panel")],
    ])


def manager_control_keyboard(telegram_id: int, is_active: int):
    buttons = []

    if is_active:
        buttons.append(
            InlineKeyboardButton(
                text="⛔ تعطيل",
                callback_data=f"manager:disable:{telegram_id}"
            )
        )
    else:
        buttons.append(
            InlineKeyboardButton(
                text="✅ تفعيل",
                callback_data=f"manager:enable:{telegram_id}"
            )
        )

    return InlineKeyboardMarkup(inline_keyboard=[
        buttons,
        [InlineKeyboardButton(text="⬅️ رجوع", callback_data="manager:list")]
    ])


# ======================
# Handlers
# ======================
@router.callback_query(F.data == "admin:panel")
async def admin_panel(callback: CallbackQuery):
    if not is_super_admin(callback.from_user.id):
        await callback.answer("غير مصرح", show_alert=True)
        return

    await callback.message.edit_text(
        "🔧 لوحة التحكم",
        reply_markup=admin_main_keyboard()
    )


@router.callback_query(F.data == "admin:managers")
async def managers_menu(callback: CallbackQuery):
    await callback.message.edit_text(
        "👥 إدارة المشرفين",
        reply_markup=managers_keyboard()
    )


# ======================
# Add Supervisor
# ======================
@router.callback_query(F.data == "manager:add")
async def add_manager_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AddSupervisor.waiting_for_username)
    await callback.message.edit_text(
        "📥 أرسل معرف المشرف (بدون @)\nمثال: username"
    )


@router.message(AddSupervisor.waiting_for_username)
async def add_manager_finish(message: Message, state: FSMContext, bot: Bot):
    username = message.text.strip().lstrip("@")

    if not username.isalnum():
        await message.answer("❌ معرف غير صالح")
        return

    try:
        chat = await bot.get_chat(f"@{username}")
    except Exception:
        await message.answer("❌ لم يتم العثور على مستخدم بهذا المعرف")
        return

    telegram_id = chat.id

    db.add_user(telegram_id=telegram_id, role="supervisor")

    await state.clear()
    await message.answer(
        f"✅ تم إضافة المشرف @{username} بنجاح",
        reply_markup=admin_main_keyboard()
    )


# ======================
# List Supervisors
# ======================
@router.callback_query(F.data == "manager:list")
async def list_managers(callback: CallbackQuery):
    admins = db.get_admins()

    if not admins:
        await callback.message.edit_text(
            "لا يوجد مشرفون حاليًا",
            reply_markup=managers_keyboard()
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


# ======================
# Manager Control
# ======================
@router.callback_query(F.data.startswith("manager:view:"))
async def manager_view(callback: CallbackQuery):
    telegram_id = int(callback.data.split(":")[-1])
    user = db.get_user_by_telegram_id(telegram_id)

    await callback.message.edit_text(
        f"👤 المشرف: {telegram_id}\nالحالة: {'مفعل' if user['is_active'] else 'معطل'}",
        reply_markup=manager_control_keyboard(
            telegram_id,
            user["is_active"]
        )
    )


@router.callback_query(F.data.startswith("manager:disable:"))
async def disable_manager(callback: CallbackQuery):
    telegram_id = int(callback.data.split(":")[-1])
    db.set_user_active(telegram_id, 0)
    await callback.answer("تم التعطيل")
    await manager_view(callback)


@router.callback_query(F.data.startswith("manager:enable:"))
async def enable_manager(callback: CallbackQuery):
    telegram_id = int(callback.data.split(":")[-1])
    db.set_user_active(telegram_id, 1)
    await callback.answer("تم التفعيل")
    await manager_view(callback)
