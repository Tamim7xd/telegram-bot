from telegram import Update

from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)

from config import TOKEN, ADMIN_ID

from db import init_db

from core.users import (
    register,
    get,
    add_message
)

from core.ui import admin_menu

from core.callbacks import callback_handler

from core.state import (
    get_state,
    clear_state
)

from core.actions import (
    add_money,
    remove_money,
    set_title
)

from core.questions import random_question


active_questions = {}


# =========================
# START
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    register(update.effective_user)

    await update.message.reply_text(
        "🚀 البوت يعمل"
    )


# =========================
# ADMIN PANEL
# =========================
async def adminpy(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != ADMIN_ID:
        return

    await update.message.reply_text(
        "🛠 لوحة التحكم",
        reply_markup=admin_menu()
    )


# =========================
# MESSAGES
# =========================
async def messages(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user

    text = update.message.text.lower()

    register(user)

    # =========================
    # STATE SYSTEM
    # =========================
    state = get_state(user.id)

    if state:

        action = state["action"]

        target = state["target"]

        if action == "add":

            add_money(target, int(text))

            await update.message.reply_text(
                "✅ تم إضافة المال"
            )

            clear_state(user.id)

            return

        elif action == "rem":

            remove_money(target, int(text))

            await update.message.reply_text(
                "✅ تم الخصم"
            )

            clear_state(user.id)

            return

        elif action == "title":

            set_title(target, text)

            await update.message.reply_text(
                "🏆 تم تعديل اللقب"
            )

            clear_state(user.id)

            return

    # =========================
    # ADD MESSAGE
    # =========================
    add_message(user.id)

    # =========================
    # MONEY
    # =========================
    if text in ["فلوسي", "فلوس"]:

        u = get(user.id)

        await update.message.reply_text(
f"""
💰 فلوسك الحالية

{u[3]:,} دينار عراقي
"""
        )

        return

    # =========================
    # INFO
    # =========================
    if text in ["معلوماتي", "معلومات"]:

        u = get(user.id)

        await update.message.reply_text(
f"""
👤 معلومات العضو

💰 المال:
{u[3]:,}

📨 الرسائل:
{u[2]:,}

🏆 اللقب:
{u[8]}
"""
        )

        return

    # =========================
    # QUESTION
    # =========================
    if text in ["سؤال", "سوال"]:

        q = random_question()

        active_questions[user.id] = q["answer"].lower()

        await update.message.reply_text(
f"""
❓ سؤال جديد

{q['question']}

💰 الجائزة 250 دينار
"""
        )

        return

    # =========================
    # ANSWER
    # =========================
    if user.id in active_questions:

        answer = active_questions[user.id]

        if text == answer:

            add_money(user.id, 250)

            await update.message.reply_text(
                "🎉 إجابة صحيحة +250"
            )

        else:

            await update.message.reply_text(
                "❌ إجابة خاطئة"
            )

        del active_questions[user.id]


# =========================
# MAIN
# =========================
def main():

    init_db()

    app = Application.builder().token(TOKEN).build()

    app.add_handler(
        CommandHandler(
            "start",
            start
        )
    )

    app.add_handler(
        CommandHandler(
            "adminpy",
            adminpy
        )
    )

    app.add_handler(
        CallbackQueryHandler(callback_handler)
    )

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            messages
        )
    )

    print("🚀 BOT RUNNING")

    app.run_polling()


if __name__ == "__main__":
    main()
