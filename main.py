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
    add_message,
    get_title,
    format_money,
    next_goal
)

from core.questions import random_q

from core.callbacks import (
    users_page,
    user_panel
)

from db import c, conn

import random


# ================= ACTIVE QUESTION =================
active_q = {}


# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    register(update.effective_user)

    await update.message.reply_text("🚀 بوت التحديات الفخم يعمل")


# ================= ADMIN PANEL (مستبدل بالكامل) =================
async def adminpy(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != ADMIN_ID:
        return

    await update.message.reply_text("🛠 تم فتح لوحة الأدمن (سيتم ربط الأزرار في callbacks)")


# ================= ASK QUESTION =================
async def ask_question(update: Update, context: ContextTypes.DEFAULT_TYPE):

    q = random_q()

    active_q[update.effective_user.id] = q[1].lower()

    await update.message.reply_text(
f"""
❓ سؤال:

{q[0]}

💰 الجائزة: 250 دينار
"""
    )


# ================= HANDLE TEXT =================
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not update.message:
        return

    user = update.effective_user
    text = update.message.text.strip().lower()

    register(user)
    add_message(user.id)

    data = get(user.id)

    # ================= ANSWER QUESTION =================
    if user.id in active_q:

        correct = active_q[user.id]

        if text == correct:

            c.execute("""
            UPDATE users
            SET money = money + 250,
                rewards = rewards + 1
            WHERE user_id=?
            """, (user.id,))

            conn.commit()

            await update.message.reply_text("🎉 صحيح +250 دينار 💰")

        else:

            await update.message.reply_text(f"❌ خطأ! الإجابة الصحيحة: {correct}")

        del active_q[user.id]
        return


    # ================= MONEY =================
    if text in ["فلوسي", "فلوس"]:

        await update.message.reply_text(
            f"💰 {format_money(data[3])} دينار"
        )
        return


    # ================= TITLE =================
    if text in ["لقبي", "لقب"]:

        await update.message.reply_text(
            f"🏆 {get_title(data[2])}"
        )
        return


    # ================= INFO =================
    if text in ["معلوماتي", "معلومات"]:

        await update.message.reply_text(
f"""
👤 الاسم: {data[1]}
💬 الرسائل: {data[2]}
💰 الفلوس: {format_money(data[3])}
🏆 اللقب: {get_title(data[2])}
"""
        )
        return


    # ================= QUESTION =================
    if text in ["سؤال", "سوال"]:

        await ask_question(update, context)
        return


# ================= CALLBACK HANDLER =================
async def callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    data = query.data

    # إغلاق
    if data == "close":
        await query.message.delete()
        return

    # قائمة الأعضاء
    if data.startswith("users_"):

        page = int(data.split("_")[1])

        await query.message.edit_text(
            "👥 قائمة الأعضاء",
            reply_markup=users_page(page)
        )
        return

    # ملف عضو
    if data.startswith("user_"):

        parts = data.split("_")

        uid = int(parts[1])
        page = int(parts[2])

        text, kb = user_panel(uid, page)

        await query.message.edit_text(text, reply_markup=kb)
        return

    # إحصائيات
    if data == "stats":

        c.execute("""
        SELECT COUNT(*), SUM(messages), SUM(money)
        FROM users
        """)

        s = c.fetchone()

        await query.message.edit_text(
f"""
📊 الإحصائيات

👥 الأعضاء: {s[0]}
💬 الرسائل: {s[1] or 0}
💰 الأموال: {s[2] or 0}
"""
        )
        return


# ================= MAIN =================
def main():

    init_db()

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("adminpy", adminpy))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

    # ✅ هذا هو الـ callback handler الحقيقي المطابق لمشروعك
    app.add_handler(CallbackQueryHandler(callbacks))

    print("🚀 BOT RUNNING")

    app.run_polling()


if __name__ == "__main__":
    main()
