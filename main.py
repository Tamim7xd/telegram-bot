import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand
from config import BOT_TOKEN
from db import db
from core.bot_core import setup_bot
from core.users import register_user_handlers
from core.xp import register_xp_handlers
from core.titles import register_titles_handlers
from core.games import register_games_handlers
from core.events import register_event_handlers
from core.callbacks import register_callback_handlers
from core.notify import register_notify_handlers

logging.basicConfig(level=logging.INFO)

async def set_commands(bot: Bot):
    commands = [
        BotCommand(command="start", description="بدء البوت"),
        BotCommand(command="adminiq", description="لوحة الأدمن"),
    ]
    await bot.set_my_commands(commands)

async def main():
    await db.connect()
    await db.init_tables()
    bot = Bot(token=BOT_TOKEN)
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
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
