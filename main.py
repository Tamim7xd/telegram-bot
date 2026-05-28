from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

from config import TOKEN
from db import init_db

from core.users import register, get, add_xp, get_title
from core.questions import random_q, set_q, get_q, del_q
from core.admin import notify, is_admin

# ========= START =========
async def start(update: Update, context):
    register(update.effective_user)
    await update.message.reply_text("🚀 بوت التحديات الفخم يعمل")

# ========= INFO =========
async def info(update: Update, context):
    u = get(update.effective_user.id)
    title = get_title(u[2])

    await update.message.reply_text(
        f"👤 {u[1]}\n"
        f"⭐ XP: {u[2]}\n"
        f"🏆 اللقب: {title}"
    )

# ========= QUESTION =========
async def ask(update: Update, context):
    q, a = random_q()
    set_q(update.effective_user.id, a)
    await update.message.reply_text(f"❓ {q}")

# ========= HANDLE =========
async def handle(update: Update, context):
    u = update.effective_user
    register(u)

    add_xp(u.id, 1)

    ans = get_q(u.id)

    if ans:
        user_ans = update.message.text.lower().strip()
        correct = ans[0].lower().strip()

        if user_ans == correct:
            add_xp(u.id, 10)
            await update.message.reply_text(
                "🎉🔥 إجابة صحيحة!\n+10 XP"
            )
            await notify(context.bot, f"{u.first_name} أجاب صحيح")
        else:
            await update.message.reply_text(
                f"❌ خطأ!\n✔ الإجابة الصحيحة: {ans[0]}"
            )

        del_q(u.id)

# ========= BROADCAST + PIN =========
async def broadcast(update: Update, context):
    if not is_admin("admin"):
        return

    text = " ".join(context.args)
    name = update.effective_user.first_name

    msg = await context.bot.send_message(
        chat_id=GROUP_ID,
        text=f"📢 إعلان فخم\n👤 {name}\n\n{text}"
    )

    try:
        await context.bot.pin_chat_message(GROUP_ID, msg.message_id)
    except:
        pass

    await notify(context.bot, f"📢 إعلان جديد من {name}")
    await update.message.reply_text("📌 تم النشر والتثبيت")

# ========= RUN =========
def main():
    init_db()

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("info", info))
    app.add_handler(CommandHandler("gg", ask))
    app.add_handler(CommandHandler("broadcast", broadcast))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

    print("🔥 FANCY BOT RUNNING")
    app.run_polling()

if __name__ == "__main__":
    main()
