import logging
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes
)

from config import BOT_TOKEN, GROUP_ID
from core.bot_core import callback_handler, is_admin, create_user, add_message, add_xp
from core.game_engine import check_answer, start_game


# =========================
# LOGGING
# =========================
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)


# =========================
# START
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    create_user(user.id, user.first_name)

    await update.message.reply_text("👋 أهلاً بك في البوت!")


# =========================
# MESSAGE HANDLER
# =========================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user

    create_user(user.id, user.first_name)
    add_message(user.id)

    # نظام الألعاب
    await check_answer(context.bot, update.message)


# =========================
# ADMIN COMMAND (اختياري)
# =========================
async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user

    if not is_admin(user.id):
        return

    await update.message.reply_text("""
🛠 لوحة الأدمن

👥 المستخدمين
🏆 الترتيب
📊 الإحصائيات
📢 إرسال للجميع
""")


# =========================
# GAME COMMAND
# =========================
async def game(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not is_admin(update.message.from_user.id):
        return

    await start_game(context.bot, update.message.chat_id)


# =========================
# MAIN
# =========================
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    # أوامر
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin))
    app.add_handler(CommandHandler("game", game))

    # رسائل
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # أزرار
    app.add_handler(CallbackQueryHandler(callback_handler))

    print("🚀 BOT RUNNING...")

    app.run_polling()


if __name__ == "__main__":
    main()
