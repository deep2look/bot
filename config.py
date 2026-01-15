# config.py

import os


# ======================
# Telegram Bot Settings
# ======================

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is not set in environment variables")

SUPER_ADMIN_ID = os.getenv("SUPER_ADMIN_ID")
if not SUPER_ADMIN_ID:
    raise RuntimeError("SUPER_ADMIN_ID is not set in environment variables")

try:
    SUPER_ADMIN_ID = int(SUPER_ADMIN_ID.strip())
except ValueError:
    # If there are spaces or invalid characters, try to extract digits
    import re
    digits = re.findall(r'\d+', SUPER_ADMIN_ID)
    if digits:
        SUPER_ADMIN_ID = int("".join(digits))
    else:
        raise RuntimeError(f"Invalid SUPER_ADMIN_ID format: {SUPER_ADMIN_ID}")


# ======================
# Database Settings
# ======================

DATABASE_NAME = os.getenv("DATABASE_NAME", "bot.db")


# ======================
# General Settings
# ======================

BOT_NAME = os.getenv("BOT_NAME", "Dynamic Admin Bot")
DEBUG = os.getenv("DEBUG", "true").lower() == "true"
