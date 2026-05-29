import asyncio
from aiogram import Bot, Dispatcher

from config import BOT_TOKEN
from Core_.bot_core import setup


async def main():

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    setup(dp)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
