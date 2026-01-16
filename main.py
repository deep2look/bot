import asyncio
import logging
import threading
from flask import Flask

from bot import main  # دالة main الخاصة بالبوت

# ===== Keep Alive Server =====
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is alive!"

def run_web():
    # مهم: 0.0.0.0 و 8080 للعمل مع Replit
    app.run(host="0.0.0.0", port=8080)

# تشغيل السيرفر في Thread منفصل
threading.Thread(target=run_web, daemon=True).start()

# ===== Bot Runner =====
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot stopped")
    except Exception as e:
        logging.error(f"Critical error: {e}")

