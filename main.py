from telegram import Update
from telegram.ext import Application, MessageHandler, CallbackQueryHandler, ContextTypes, filters

from config import TOKEN, ADMIN_ID
from db import init_db

from core.users import register, get
from core.callbacks import callback_handler
from core.state import get_state, clear_state
from core.actions import add_money, remove_money, set_title
from core.xp import add_xp, get_progress
from core.titles import TITLES


# ───────── USER MESSAGES ─────────
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user
    text = update.message.text.lower()

    register(user)

    # XP + money
    xp, level = add_xp(user.id, 25)

    u = get(user.id)
    title = TITLES[min(level, len(TITLES)-1)]

    # update title
    c.execute("UPDATE users SET title=? WHERE user_id=?", (title, user.id))
    from db import conn
    conn.commit()

    # ───── STATE ─────
    state = get_state(user.id)

    if state:

        if state["action"] == "add":
            add_money(state["target"], int(text))
            await update.message.reply_text("✅ تم إضافة المال")

        elif state["action"] == "rem":
            remove_money(state["target"], int(text))
            await update.message.reply_text("✅ تم الخصم")

        elif state["action"] == "title":
            set_title(state["target"], text)
            await update.message.reply_text("🏆 تم تعديل اللقب")

        clear_state(user.id)
        return

    # ───── USER COMMANDS ─────
    if text in ["فلوسي", "فلوس"]:
        await update.message.reply_text(f"💰 {u[3]}")

    if text in ["معلوماتي", "معلومات"]:
        xp, level, need, percent, bar = get_progress(user.id)

        await update.message.reply_text(
f"""👤 معلوماتك

💰 {u[3]}
⭐ {xp}/{need}
📊 LVL {level}
🏆 {u[8]}
{bar} {percent}%"""
        )


# ───────── MAIN ─────────
def main():

    init_db()

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🚀 BOT RUNNING FULL SYSTEM")

    app.run_polling()


if __name__ == "__main__":
    main()
