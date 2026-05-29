from aiogram import Bot, Dispatcher
from config import BOT_TOKEN

from _core.bot_core import setup_bot
from _core.notify import set_bot_instance

import asyncio

async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    set_bot_instance(bot)

    setup_bot(dp)

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
