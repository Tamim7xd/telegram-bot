from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

from config import TOKEN, ADMIN_ID, GROUP_ID
from db import init_db

from core.users import register, add_xp, get, get_title
from core.questions import random_q, set_q, get_q, del_q
from core.admin import is_admin, is_admin, set_role, notify

# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    register(update.effective_user)
    await update.message.reply_text("🚀 بوت التحديات الفخم يعمل")

# ================= INFO =================
async def info(update: Update, context):
    u = get(update.effective_user.id)
    title = get_title(u[2])
    await update.message.reply_text(f"👤 {u[1]}\n⭐ XP: {u[2]}\n🏆 {title}")

# ================= QUESTION =================
async def ask(update: Update, context):
    q, a = random_q()
    set_q(update.effective_user.id, a)
    await update.message.reply_text(f"❓ {q}")

# ================= HANDLE =================
async def handle(update: Update, context):
    u = update.effective_user
    register(u)

    add_xp(u.id, 1)

    ans = get_q(u.id)

    if ans:
        if update.message.text.lower().strip() == ans[0].lower():
            add_xp(u.id, 10)
            await update.message.reply_text("🎉 صحيح +10 XP 🔥")
            await notify(context.bot, f"{u.first_name} أجاب صح")
        else:
            await update.message.reply_text(f"❌ خطأ! الصحيح: {ans[0]}")

        del_q(u.id)

# ================= BROADCAST =================
async def broadcast(update: Update, context):
    if not is_admin(update.effective_user.id):
        return

    text = " ".join(context.args)

    msg = await context.bot.send_message(
        GROUP_ID,
        f"📢 إعلان\n\n{text}"
    )

    try:
        await context.bot.pin_chat_message(GROUP_ID, msg.message_id)
    except:
        pass

# ================= ADMIN COMMANDS =================
async def setadmin(update: Update, context):
    if update.effective_user.id != ADMIN_ID:
        return

    uid = int(context.args[0])
    set_role(uid, "admin")
    await update.message.reply_text("تم رفعه Admin")

async def setmod(update: Update, context):
    if update.effective_user.id != ADMIN_ID:
        return

    uid = int(context.args[0])
    set_role(uid, "mod")
    await update.message.reply_text("تم رفعه Mod")

# ================= RUN =================
def main():
    init_db()

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("info", info))
    app.add_handler(CommandHandler("ss", ask))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(CommandHandler("setadmin", setadmin))
    app.add_handler(CommandHandler("setmod", setmod))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

    print("🚀 BOT FULL RUNNING")
    app.run_polling()

if __name__ == "__main__":
    main()
