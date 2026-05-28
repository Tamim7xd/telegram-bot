from telegram import Update
from telegram.ext import Application, MessageHandler, CallbackQueryHandler, filters, ContextTypes

from config import TOKEN
from db import init_db
from core.callbacks import callback_handler


async def test_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("MESSAGE:", update.message.text)
    await update.message.reply_text("OK")


def main():

    init_db()

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, test_message))

    print("BOT RUNNING")
    app.run_polling()


if __name__ == "__main__":
    main()
