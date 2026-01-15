# bot.py

import asyncio
import logging

from aiogram import Bot, Dispatcher, Router
from aiogram.filters import CommandStart
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

from config import BOT_TOKEN, SUPER_ADMIN_ID
from database import Database
from aiogram.fsm.storage.memory import MemoryStorage
from admin_interface import router as admin_router
from user_interface import router as user_router
from keyboards import admin_main_keyboard, main_menu_keyboard


from aiogram.fsm.context import FSMContext

# ======================
# Logging
# ======================
logging.basicConfig(level=logging.INFO)


# ======================
# Core objects
# ======================
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
db = Database()


# ======================
# Startup
# ======================
async def on_startup():
    db.add_user(telegram_id=SUPER_ADMIN_ID, role="super_admin")
    logging.info("Super admin ready")


# ======================
# Main
# ======================
async def main():
    await on_startup()
    dp.include_router(admin_router)
    dp.include_router(user_router)
    
    # Simple start handler inside bot.py to avoid circular import
    @dp.message(CommandStart())
    async def start_handler(message: Message):
        telegram_id = message.from_user.id
        db.add_user(telegram_id=telegram_id)
        user = db.get_user_by_telegram_id(telegram_id)
        is_admin = user["role"] in ("super_admin", "admin", "supervisor")
        await message.answer(
            f"👋 مرحبًا بك {message.from_user.full_name}\n"
            "المحتوى سيظهر هنا عند تفعيله من الإدارة.",
            reply_markup=main_menu_keyboard(is_admin=is_admin)
        )

    @dp.message(lambda message: message.text == "🔄 تحديث البوت")
    async def refresh_bot_handler(message: Message):
        await start_handler(message)

    @dp.message(lambda message: message.text == "🔧 لوحة التحكم")
    async def admin_panel_handler(message: Message):
        telegram_id = message.from_user.id
        user = db.get_user_by_telegram_id(telegram_id)
        if user["role"] in ("super_admin", "admin", "supervisor"):
            await message.answer(
                "🔧 أهلاً بك في لوحة التحكم العلوية",
                reply_markup=admin_main_keyboard()
            )
        else:
            await message.answer("عذراً، ليس لديك صلاحية الوصول.")

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
