from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler

from config import TOKEN, ADMIN_ID, GROUP_ID
from db import c, conn
from core import users
from core.users import get_question

app = Application.builder().token(TOKEN).build()

admin_state = {}
active_questions = {}

# 👥 قائمة أعضاء بدون ID
def users_keyboard(action):
    c.execute("SELECT user_id, name FROM users LIMIT 20")
    rows = c.fetchall()

    return InlineKeyboardMarkup([
        [InlineKeyboardButton(r[1], callback_data=f"{action}_{r[0]}")]
        for r in rows
    ])

# 👑 لوحة الأدمن
async def admin(update, context):

    if update.effective_user.id != ADMIN_ID:
        return

    keyboard = [
        [InlineKeyboardButton("💰 فلوس", callback_data="money")],
        [InlineKeyboardButton("🏷️ لقب", callback_data="title")],
        [InlineKeyboardButton("🚫 حظر", callback_data="ban")],
        [InlineKeyboardButton("🔇 كتم", callback_data="mute")],
    ]

    await update.message.reply_text("👑 لوحة الأدمن", reply_markup=InlineKeyboardMarkup(keyboard))


# 🔘 الأزرار
async def buttons(update, context):

    q = update.callback_query
    await q.answer()

    uid = q.from_user.id
    data = q.data

    if uid != ADMIN_ID:
        return

    if data == "money":
        await q.message.reply_text("💰 اختر العضو:", reply_markup=users_keyboard("money"))

    if data == "title":
        await q.message.reply_text("🏷️ اختر العضو:", reply_markup=users_keyboard("title"))

    if data == "ban":
        await q.message.reply_text("🚫 اختر العضو:", reply_markup=users_keyboard("ban"))

    if data == "mute":
        await q.message.reply_text("🔇 اختر العضو:", reply_markup=users_keyboard("mute"))


    if data.startswith("money_"):
        target = int(data.split("_")[1])
        admin_state[uid] = f"money_{target}"
        await q.message.reply_text("💰 اكتب المبلغ")

    if data.startswith("title_"):
        target = int(data.split("_")[1])
        admin_state[uid] = f"title_{target}"
        await q.message.reply_text("🏷️ اكتب اللقب")

    if data.startswith("ban_"):
        target = int(data.split("_")[1])
        c.execute("UPDATE users SET banned=1 WHERE user_id=?", (target,))
        conn.commit()
        await context.bot.send_message(GROUP_ID, f"🚫 تم حظر {target}")

    if data.startswith("mute_"):
        target = int(data.split("_")[1])
        import time
        c.execute("UPDATE users SET muted_until=? WHERE user_id=?",
                  (int(time.time()) + 300, target))
        conn.commit()
        await context.bot.send_message(GROUP_ID, f"🔇 تم كتم {target} 5 دقائق")


# 💬 الرسائل
async def handle(update, context):

    text = update.message.text
    uid = update.effective_user.id

    if users.is_banned(uid):
        return

    if users.is_muted(uid):
        return

    users.reg(update.effective_user)

    t = text.lower().strip()

    # ❓ سؤال / سوال
    if t in ["سؤال","سوال","اسأل","سؤالي"]:

        qst = get_question()

        active_questions[uid] = qst

        await update.message.reply_text(
            f"❓ {qst['q']}\n\n✍️ اكتب الإجابة"
        )
        return

    # ✅ إجابة
    if uid in active_questions:

        qst = active_questions[uid]

        if t == qst["a"].lower():

            c.execute("UPDATE users SET money=money+5 WHERE user_id=?", (uid,))
            conn.commit()

            await update.message.reply_text("✅ إجابة صحيحة +5 💰")

            await context.bot.send_message(
                GROUP_ID,
                f"🎉 {update.effective_user.first_name} أجاب صح +5 فلوس"
            )
        else:
            await update.message.reply_text("❌ إجابة خاطئة")

        active_questions.pop(uid)
        return


    res = users.handle_user(text, update)
    if res:
        await update.message.reply_text(res)


app.add_handler(CommandHandler("admin", admin))
app.add_handler(CallbackQueryHandler(buttons))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

print("BOT RUNNING")
app.run_polling()
