from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

from config import TOKEN
from db import init_db

from core.users import register, get, add_xp, get_title
from core.questions import random_q, set_q, get_q, del_q
from core.admin import notify

# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    register(update.effective_user)

    await update.message.reply_text(
        "🚀 أهلاً بك في بوت التحديات الفخم\n"
        "اكتب /سؤال لبدء اللعب 🎮"
    )

# ================= INFO =================
async def info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = get(update.effective_user.id)
    title = get_title(u[2])

    await update.message.reply_text(
        f"👤 الاسم: {u[1]}\n"
        f"⭐ XP: {u[2]}\n"
        f"🏆 اللقب: {title}"
    )

# ================= QUESTION =================
async def ask(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q, a = random_q()

    set_q(update.effective_user.id, a)

    await update.message.reply_text(f"❓ {q}")

# ================= HANDLE TEXT =================
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    u = update.effective_user
    register(u)

    add_xp(u.id, 1)

    ans = get_q(u.id)

    if ans:
        user_answer = update.message.text.lower().strip()
        correct = ans[0].lower().strip()

        if user_answer == correct:
            add_xp(u.id, 10)
            await update.message.reply_text("🎉 صحيح +10 XP 🔥")
            await notify(context.bot, f"🔥 {u.first_name} أجاب صحيح")
        else:
            await update.message.reply_text(f"❌ خطأ!\n✔ الصحيح: {ans[0]}")

        del_q(u.id)

# ================= RUN =================
def main():
    init_db()

    app = Application.builder().token(TOKEN).build()

    # 🔥 مهم جدًا: ربط الأوامر
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("info", info))
    app.add_handler(CommandHandler("سؤال", ask))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

    print("🚀 BOT RUNNING SUCCESSFULLY")
    app.run_polling()

if __name__ == "__main__":
    main()
