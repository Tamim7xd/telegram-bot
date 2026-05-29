import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand, ChatMemberUpdated
from config import BOT_TOKEN, ADMIN_IDS
from db import db
from _core.bot_core import setup_bot
from _core.users import get_or_create_user, register_user_handlers
from _core.xp import register_xp_handlers
from _core.titles import register_titles_handlers
from _core.games import register_games_handlers
from _core.events import register_event_handlers
from _core.callbacks import register_callback_handlers
from _core.notify import register_notify_handlers, set_bot_instance, bot

logging.basicConfig(level=logging.INFO)

async def set_commands(bot: Bot):
    await bot.set_my_commands([
        BotCommand(command="start", description="بدء البوت"),
        BotCommand(command="adminiq", description="لوحة الأدمن")
    ])

async def on_user_join(event: ChatMemberUpdated):
    if event.new_chat_member.status == "member" and event.old_chat_member.status != "member":
        user = event.new_chat_member.user
        await get_or_create_user(user)
        await bot.send_message(event.chat.id, f"✨ مرحباً {user.full_name}!\nاستخدم #ملفي لعرض معلوماتك.")

async def main():
    await db.connect()
    await db.init_tables()
    bot_obj = Bot(token=BOT_TOKEN)
    set_bot_instance(bot_obj)
    dp = Dispatcher()

    setup_bot(dp)
    register_user_handlers(dp)
    register_xp_handlers(dp)
    register_titles_handlers(dp)
    register_games_handlers(dp)
    register_event_handlers(dp)
    register_callback_handlers(dp)
    register_notify_handlers(dp)

    dp.chat_member.register(on_user_join)

    await set_commands(bot_obj)
    print(f"✅ البوت يعمل. الأدمن: {ADMIN_IDS}")
    await dp.start_polling(bot_obj)

if __name__ == "__main__":
    asyncio.run(main())
