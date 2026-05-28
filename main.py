import logging
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters

from config import BOT_TOKEN, ADMIN_ID
from core.service import create_user, add_message, is_admin
from core.bot_core import callback_handler
from core.game_engine import check_answer, start_game


logging.basicConfig(level=logging.INFO)


async def start(update, context):
    user = update.message.from_user
    create_user(user.id, user.first_name)
    await update.message.reply_text("👋 أهلاً بك")


async def handle_message(update, context):

    user = update.message.from_user
    create_user(user.id, user.first_name)
    add_message(user.id)

    await check_answer(context.bot, update.message)


async def admin(update, context):

    if update.message.from_user.id != ADMIN_ID:
        return

    await update.message.reply_text("🛠 لوحة الأدمن")


def main():

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(callback_handler))

    print("BOT RUNNING")
    app.run_polling()


if __name__ == "__main__":
    main()
