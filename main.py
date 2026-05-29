import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand
from config import BOT_TOKEN
from db import db
from _core.bot_core import setup_bot
from _core.users import register_user_handlers
from _core.xp import register_xp_handlers
from _core.titles import register_titles_handlers
from _core.games import register_games_handlers
from _core.events import register_event_handlers
from _core.callbacks import register_callback_handlers
from _core.notify import register_notify_handlers, set_bot_instance

logging.basicConfig(level=logging.INFO)

async def set_commands(bot: Bot):
    await bot.set_my_commands([
        BotCommand(command="start", description="بدء البوت"),
        BotCommand(command="adminiq", description="لوحة الأدمن")
    ])

async def main():
    await db.connect()
    await db.init_tables()
    bot = Bot(token=BOT_TOKEN)
    set_bot_instance(bot)
    dp = Dispatcher()
    
    setup_bot(dp)
    register_user_handlers(dp)
    register_xp_handlers(dp)
    register_titles_handlers(dp)
    register_games_handlers(dp)
    register_event_handlers(dp)
    register_callback_handlers(dp)
    register_notify_handlers(dp)
    
    await set_commands(bot)
    print("✅ البوت يعمل الآن بكل الميزات")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
