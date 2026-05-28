from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

from config import TOKEN, ADMIN_ID
from db import init_db
from core.ui import admin_menu
from core.callbacks import callback_handler
from core.users import register
from core.questions import random_q
from core.xp import xp_add, get_progress
from core.titles import get_title

active_q = {}

async def start(update: Update, context):
    register(update.effective_user)
    await update.message.reply_text("🚀 البوت يعمل")

async def adminpy(update: Update, context):
    if update.effective_user.id != ADMIN_ID:
        return

    await update.message.reply_text("🛠 لوحة الأدمن", reply_markup=admin_menu())

async def handle(update: Update, context):

    user = update.effective_user
    text = update.message.text.lower()

    register(user)

    if text in ["سؤال","سوال"]:
        q = random_q()
        active_q[user.id] = q[1].lower()
        await update.message.reply_text(q[0])
        return

    if user.id in active_q:
        if text == active_q[user.id]:

            leveled, level = xp_add(user.id, 25)

            xp, lvl, need, percent, bar = get_progress(user.id)
            title = get_title(lvl)

            await update.message.reply_text(
f"""🎉 صحيح
💰 +250
⭐ +25 XP

🏆 {title}
📊 {bar} {percent}%"""
            )

            if leveled:
                await update.message.reply_text("🚀 ترقية مستوى!")

        else:
            await update.message.reply_text("❌ خطأ")

        del active_q[user.id]

def main():
    init_db()

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("adminpy", adminpy))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
    app.add_handler(CallbackQueryHandler(callback_handler))

    print("🚀 BOT FULL SYSTEM RUNNING")
    app.run_polling()

if __name__ == "__main__":
    main()
