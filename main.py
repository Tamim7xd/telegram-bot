from telegram import (
    Update
)

from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

from config import (
    TOKEN,
    GROUP_ID,
    ADMIN_ID
)

from db import (
    init_db,
    conn,
    c
)

from core.users import (
    register,
    get,
    add_message,
    get_title,
    format_money,
    next_goal
)

from core.ui import (
    profile_text
)

from core.questions import (
    QUESTIONS
)

import random


# ================= QUESTIONS CACHE =================
active_questions = {}


# ================= SEND GROUP =================
async def group_notify(bot, text):

    if GROUP_ID != 0:

        try:
            await bot.send_message(
                chat_id=GROUP_ID,
                text=text
            )

        except:
            pass


# ================= START =================
async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    register(update.effective_user)

    await update.message.reply_text(
        "🚀 البوت الاحترافي يعمل بنجاح"
    )


# ================= USER INFO =================
async def send_info(message, uid):

    user = get(uid)

    if not user:
        return

    await message.reply_text(
        profile_text(user)
    )


# ================= ASK QUESTION =================
async def ask_question(message, uid):

    q = random.choice(QUESTIONS)

    active_questions[uid] = q[1].lower()

    await message.reply_text(
f"""
╭━━━❰ ❓ سؤال جديد ❱━━━╮

📚 السؤال:

{q[0]}

💰 الجائزة:
250 دينار عراقي

╰━━━━━━━━━━━━━━╯
"""
    )


# ================= HANDLE =================
async def handle(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not update.message:
        return

    user = update.effective_user

    text = update.message.text.strip()

    register(user)

    add_message(user.id)

    data = get(user.id)

    # ================= QUESTION ANSWER =================
    if user.id in active_questions:

        answer = active_questions[user.id]

        if text.lower() == answer:

            c.execute("""
            UPDATE users
            SET
                money = money + 250,
                rewards = rewards + 1
            WHERE user_id=?
            """, (user.id,))

            conn.commit()

            await update.message.reply_text(
f"""
🎉 إجابة صحيحة !

💰 حصلت على:
250 دينار عراقي

🔥 استمر أيها الأسطورة
"""
            )

        else:

            await update.message.reply_text(
f"""
❌ إجابة خاطئة

✅ الإجابة الصحيحة:
{answer}
"""
            )

        del active_questions[user.id]

        return


    # ================= MONEY =================
    if text in [
        "فلوسي",
        "فلوس"
    ]:

        await update.message.reply_text(
f"""
💰 فلوسك الحالية:

{format_money(data[3])} دينار عراقي
"""
        )

        return


    # ================= TITLE =================
    if text in [
        "لقبي",
        "لقب"
    ]:

        title = get_title(
            data[2],
            data[6],
            data[7]
        )

        await update.message.reply_text(
f"""
🏆 لقبك الحالي:

{title}
"""
        )

        return


    # ================= MESSAGES =================
    if text in [
        "رسائلي",
        "رسايلي",
        "رسائل",
        "رسايل"
    ]:

        await update.message.reply_text(
f"""
💬 عدد رسائلك:

{data[2]}
"""
        )

        return


    # ================= INFO =================
    if text in [
        "معلوماتي",
        "معلومات"
    ]:

        await send_info(
            update.message,
            user.id
        )

        return


    # ================= QUESTION =================
    if text in [
        "سؤال",
        "سوال"
    ]:

        await ask_question(
            update.message,
            user.id
        )

        return


    # ================= LEVEL UP =================
    messages = data[2]

    if messages == 100 or (
        messages > 100
        and
        (messages - 100) % 250 == 0
    ):

        title = get_title(
            data[2],
            data[6],
            data[7]
        )

        remain = next_goal(messages)

        await update.message.reply_text(
f"""
╔═══❰ 🏆 ترقية جديدة ❱═══╗

🎉 مبروك !

👤 العضو:
{user.first_name}

🏆 اللقب الجديد:
{title}

💬 الرسائل:
{messages}

🚀 استمر للوصول إلى القمة

╚════════════════════╝
"""
        )

        await group_notify(
            context.bot,
f"""
🏆 ترقية جديدة

👤 {user.first_name}

🎖 أصبح:
{title}
"""
        )


# ================= ADMIN PANEL =================
async def admin_panel(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if update.effective_user.id != ADMIN_ID:
        return

    await update.message.reply_text(
"""
🛠 لوحة الأدمن الاحترافية

⚙ المرحلة الحالية:
نظام المستخدمين يعمل

📌 المرحلة القادمة:
لوحة الأزرار التفاعلية
"""
    )


# ================= MAIN =================
def main():

    init_db()

    app = Application.builder().token(
        TOKEN
    ).build()

    # ================= COMMANDS =================
    app.add_handler(
        CommandHandler(
            "start",
            start
        )
    )

    app.add_handler(
        CommandHandler(
            "adminpy",
            admin_panel
        )
    )

    # ================= TEXT =================
    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle
        )
    )

    print("🚀 BOT RUNNING")

    app.run_polling()


# ================= RUN =================
if __name__ == "__main__":
    main()
