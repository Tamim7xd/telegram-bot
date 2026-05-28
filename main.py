import logging

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

from config import BOT_TOKEN
from db import c, conn

from core.service import create_user, add_message

# =========================
# LOGGING
# =========================
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# =========================
# START COMMAND
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user

    create_user(user.id, user.first_name)

    await update.message.reply_text(
        f"👋 أهلاً {user.first_name}\n"
        "🚀 البوت يعمل بنجاح"
    )


# =========================
# MESSAGE HANDLER (أساسي)
# =========================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user

    # تسجيل المستخدم
    create_user(user.id, user.first_name)

    # زيادة عدد الرسائل
    add_message(user.id)

    # أوامر بسيطة مستقبلية
    text = update.message.text.lower()

    if text == "#ملفي":
        c.execute("SELECT * FROM users WHERE user_id=?", (user.id,))
        u = c.fetchone()

        if not u:
            await update.message.reply_text("❌ لم يتم العثور على بياناتك")
            return

        await update.message.reply_text(
            f"""👤 ملفك

🆔 {u[0]}
👤 {u[1]}
💰 المال: {u[3]}
📨 الرسائل: {u[2]}
⭐ المستوى: {u[4]}
🏆 اللقب: {u[6]}
"""
        )


# =========================
# ERROR HANDLER
# =========================
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    print(f"Error: {context.error}")


# =========================
# MAIN
# =========================
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    # أوامر
    app.add_handler(CommandHandler("start", start))

    # الرسائل
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # أخطاء
    app.add_error_handler(error_handler)

    print("🚀 BOT RUNNING")
    app.run_polling()


if __name__ == "__main__":
    main()
