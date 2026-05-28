import logging

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

from config import BOT_TOKEN

from core.service import create_user, add_message, get_user
from core.events import on_message

# =========================
logging.basicConfig(level=logging.INFO)

# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    create_user(user.id, user.first_name)

    await update.message.reply_text("👋 أهلاً بك في البوت")


# =========================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user

    create_user(user.id, user.first_name)
    add_message(user.id)

    # النظام الجديد (Events)
    on_message(user.id)

    text = update.message.text.lower()

    if text == "#ملفي":
        u = get_user(user.id)

        if not u:
            await update.message.reply_text("❌ لا يوجد بيانات")
            return

        await update.message.reply_text(f"""
👤 ملفك

🆔 {u[0]}
👤 {u[1]}
💰 {u[3]}
📨 {u[2]}
⭐ {u[5]}
🔥 XP: {u[4]}
🏆 {u[6]}
""")


# =========================
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🚀 BOT RUNNING")
    app.run_polling()


if __name__ == "__main__":
    main()
