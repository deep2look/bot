import asyncio
import logging

from bot import main  # دالة تشغيل البوت (aiogram)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot stopped")
    except Exception as e:
        logging.exception("Critical error occurred")
