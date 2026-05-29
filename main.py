import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand
from config import BOT_TOKEN, ADMIN_IDS
from db import db
from _core.bot_core import setup_bot
from _core.users import register_user_handlers
from _core.xp import register_xp_handlers
from _core.titles import register_titles_handlers
from _core.games import register_games_handlers
from _core.events import register_event_handlers
from _core.callbacks import register_callback_handlers
from _core.notify import register_notify_handlers, set_bot_instance

# إعدادات التسجيل (logs) مفصلة
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

async def set_commands(bot: Bot):
    """تعيين قائمة الأوامر التي تظهر في قائمة البوت."""
    commands = [
        BotCommand(command="start", description="بدء البوت وتسجيل الدخول"),
        BotCommand(command="adminiq", description="لوحة تحكم الأدمن (للمشرفين فقط)"),
    ]
    await bot.set_my_commands(commands)
    logger.info("✅ تم تعيين أوامر البوت الظاهرة")

async def main():
    """الدالة الرئيسية لتشغيل البوت مع تأكيد تسجيل كل شيء."""
    try:
        # 1. الاتصال بقاعدة البيانات
        logger.info("🔄 جاري الاتصال بقاعدة البيانات...")
        await db.connect()
        await db.init_tables()
        logger.info("✅ تم الاتصال بقاعدة البيانات وإنشاء الجداول")
    except Exception as e:
        logger.error(f"❌ فشل الاتصال بقاعدة البيانات: {e}")
        return

    # 2. إنشاء البوت
    bot = Bot(token=BOT_TOKEN)
    set_bot_instance(bot)   # مهم لإشعارات notify.py

    # 3. إنشاء dispatcher
    dp = Dispatcher()

    # 4. تسجيل جميع المعالجات (handlers) – هذه هي الصلاحيات الكاملة
    logger.info("🔄 تسجيل معالجات البوت...")
    setup_bot(dp)                     # الأوامر الأساسية /start و /adminiq والتعامل مع #
    register_user_handlers(dp)        # دوال المستخدمين (لا تسجل أحداثاً، لكنها ضرورية)
    register_xp_handlers(dp)          # دوال الخبرات (تُستخدم داخل وحدات أخرى)
    register_titles_handlers(dp)      # دوال الألقاب
    register_games_handlers(dp)       # أزرار الألعاب ومعالجة الإجابات
    register_event_handlers(dp)       # أوامر # و $ وإضافة XP عند كل رسالة
    register_callback_handlers(dp)    # أزرار لوحة تحكم الأدمن
    register_notify_handlers(dp)      # إشعارات الترقيات والمكافآت

    logger.info("✅ تم تسجيل جميع المعالجات بنجاح")

    # 5. تعيين قائمة الأوامر الظاهرة
    await set_commands(bot)

    # 6. طباعة معلومات الأدمن عند بدء التشغيل (للتأكيد)
    if ADMIN_IDS:
        logger.info(f"👑 الأدمن المسجلون: {ADMIN_IDS}")
    else:
        logger.warning("⚠️ لم يتم تعيين أي أدمن! سيتمكن الجميع من استخدام /adminiq (غير مستحسن)")

    # 7. بدء البوت
    logger.info("🚀 بدء تشغيل البوت...")
    try:
        await dp.start_polling(bot)
    except KeyboardInterrupt:
        logger.info("🛑 تم إيقاف البوت يدوياً")
    except Exception as e:
        logger.error(f"❌ خطأ أثناء تشغيل البوت: {e}")
        raise

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 تم إنهاء البوت بواسطة Ctrl+C")
    except Exception as e:
        logger.error(f"💥 خطأ غير متوقع: {e}")
        sys.exit(1)
