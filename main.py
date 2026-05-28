from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

from config import TOKEN, ADMIN_ID
from db import init_db

from core.users import register, get
from core.ui import admin_menu
from core.callbacks import callback_handler
from core.questions import random_q
from core.xp import add_xp, get_progress
from core.titles import get_title
from core.actions import add_money, remove_money, set_title

active_q = {}

# ─────────────────────────────
# 🚀 START
# ─────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    register(update.effective_user)
    await update.message.reply_text("🚀 البوت يعمل")

# ─────────────────────────────
# 🛠 الأدمن
# ─────────────────────────────
async def adminpy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    await update.message.reply_text("🛠 لوحة الأدمن", reply_markup=admin_menu())

# ─────────────────────────────
# 🎮 USER SYSTEM (فلوسي / معلومات / سؤال)
# ─────────────────────────────
async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user
    text = update.message.text.lower()

    register(user)

    # ❓ سؤال
    if text in ["سؤال", "سوال"]:
        q = random_q()
        active_q[user.id] = q[1].lower()

        await update.message.reply_text(f"❓ {q[0]}")
        return

    # 🎯 جواب
    if user.id in active_q:

        correct = active_q[user.id]

        if text == correct:

            up, lvl = add_xp(user.id, 25)
            xp, level, need, percent, bar = get_progress(user.id)
            title = get_title(level)

            await update.message.reply_text(
f"""🎉 صحيح
💰 +250
⭐ +25 XP
🏆 {title}
📊 {bar} {percent}%"""
            )

        else:
            await update.message.reply_text("❌ خطأ")

        del active_q[user.id]
        return

    # 💰 فلوسي
    if text in ["فلوسي", "فلوس"]:
        u = get(user.id)
        await update.message.reply_text(f"💰 {u[2]}")
        return

    # 🏆 لقب
    if text in ["لقبي", "لقب"]:
        u = get(user.id)
        await update.message.reply_text(f"🏆 {u[6]}")
        return

    # 👤 معلومات
    if text in ["معلوماتي", "معلومات"]:
        u = get(user.id)

        await update.message.reply_text(
f"""👤 معلوماتك:

💰 {u[2]}
⭐ XP {u[3]}
📊 LVL {u[4]}
🏆 {u[6]}
⚠ {u[5]}"""
        )
        return

# ─────────────────────────────
# 🔐 ADMIN $ COMMANDS
# ─────────────────────────────
async def admin_commands(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user
    text = update.message.text

    if user.id != ADMIN_ID:
        return

    # 💰 $فلوس
    if text.startswith("$فلوس"):
        uid, amount = text.split()[1], text.split()[2]
        add_money(int(uid), int(amount))
        await update.message.reply_text("💰 تم إضافة فلوس")
        return

    # 💸 $خصم
    if text.startswith("$خصم"):
        uid, amount = text.split()[1], text.split()[2]
        remove_money(int(uid), int(amount))
        await update.message.reply_text("💸 تم الخصم")
        return

    # 🏆 $لقب
    if text.startswith("$لقب"):
        parts = text.split()
        uid = int(parts[1])
        title = " ".join(parts[2:])
        set_title(uid, title)
        await update.message.reply_text("🏆 تم تعديل اللقب")
        return

# ─────────────────────────────
# 🚀 MAIN
# ─────────────────────────────
def main():

    init_db()

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("adminpy", adminpy))

    app.add_handler(CallbackQueryHandler(callback_handler))

    # ⚠ مهم جدًا الترتيب
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_messages))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, admin_commands))

    print("🚀 SYSTEM RUNNING ON YOUR STRUCTURE")
    app.run_polling()

if __name__ == "__main__":
    main()
