import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand
from config import BOT_TOKEN
from db import db
from _core.bot_core import setup_bot
from _core.users import register_user_handlers
from _core.xp import register_xp_handlers
from _core.titles import register_titles_handlers   # ✅ تسجيل الألقاب
from _core.games import register_games_handlers
from _core.events import register_event_handlers
from _core.callbacks import register_callback_handlers
from _core.notify import register_notify_handlers, set_bot_instance

logging.basicConfig(level=logging.INFO)

async def set_commands(bot: Bot):
    commands = [
        BotCommand(command="start", description="بدء البوت"),
        BotCommand(command="adminiq", description="لوحة الأدمن"),
    ]
    await bot.set_my_commands(commands)

async def main():
    # الاتصال بقاعدة البيانات
    await db.connect()
    await db.init_tables()

    # إنشاء البوت
    bot = Bot(token=BOT_TOKEN)
    set_bot_instance(bot)   # للإشعارات

    dp = Dispatcher()

    # تسجيل جميع وحدات البوت (handlers)
    setup_bot(dp)                     # الأوامر الأساسية /start و /adminiq و #
    register_user_handlers(dp)        # دوال المستخدمين
    register_xp_handlers(dp)          # نظام XP والمستويات
    register_titles_handlers(dp)      # ⭐ نظام الألقاب (يجب وجوده)
    register_games_handlers(dp)       # أزرار الألعاب والإجابات
    register_event_handlers(dp)       # أوامر # و $ وإضافة XP
    register_callback_handlers(dp)    # أزرار لوحة تحكم الأدمن
    register_notify_handlers(dp)      # إشعارات الترقيات

    # تعيين أوامر البوت الظاهرة في القائمة
    await set_commands(bot)

    # بدء البوت
    print("✅ البوت يعمل الآن...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
