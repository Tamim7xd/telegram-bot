import asyncio
import logging
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN
from db import init_db

from _core.bot_core import register_core

logging.basicConfig(level=logging.INFO)

async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    init_db()

    register_core(dp, bot)

    print("BOT IS RUNNING...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
