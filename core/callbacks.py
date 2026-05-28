from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)

from telegram.ext import ContextTypes

from config import ADMIN_ID

from db import c

from core.state import set_state

from core.users import get

from core.actions import (
    mute,
    unmute,
    ban,
    unban
)


# =========================
# CALLBACK HANDLER
# =========================
async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    await query.answer()

    data = query.data

    # =========================
    # ADMIN CHECK
    # =========================
    if query.from_user.id != ADMIN_ID:

        await query.answer(
            "❌ ليس لديك صلاحية",
            show_alert=True
        )

        return

    # =========================
    # CLOSE
    # =========================
    if data == "close":

        await query.edit_message_text(
            "❌ تم إغلاق اللوحة"
        )

    # =========================
    # USERS
    # =========================
    elif data == "users":

        c.execute(
            "SELECT user_id, name FROM users LIMIT 10"
        )

        users = c.fetchall()

        keyboard = []

        for user in users:

            keyboard.append([
                InlineKeyboardButton(
                    user[1],
                    callback_data=f"user:{user[0]}"
                )
            ])

        keyboard.append([
            InlineKeyboardButton(
                "🔙 رجوع",
                callback_data="home"
            )
        ])

        await query.edit_message_text(
            "👥 قائمة الأعضاء",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    # =========================
    # STATS
    # =========================
    elif data == "stats":

        c.execute("SELECT COUNT(*) FROM users")
        members = c.fetchone()[0]

        c.execute("SELECT SUM(messages) FROM users")
        messages = c.fetchone()[0]

        c.execute("SELECT SUM(money) FROM users")
        money = c.fetchone()[0]

        await query.edit_message_text(
f"""
📊 الإحصائيات العامة

👥 الأعضاء:
{members:,}

📨 الرسائل:
{messages or 0:,}

💰 الأموال:
{money or 0:,}
"""
        )

    # =========================
    # BAD USERS
    # =========================
    elif data == "bad":

        keyboard = [

            [
                InlineKeyboardButton(
                    "🚫 المحظورين",
                    callback_data="banned"
                )
            ],

            [
                InlineKeyboardButton(
                    "🔇 المكتومين",
                    callback_data="muted"
                )
            ],

            [
                InlineKeyboardButton(
                    "🔙 رجوع",
                    callback_data="home"
                )
            ]
        ]

        await query.edit_message_text(
            "🚫 قسم المخالفين",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    # =========================
    # BANNED LIST
    # =========================
    elif data == "banned":

        c.execute(
            "SELECT user_id, name FROM users WHERE banned=1"
        )

        users = c.fetchall()

        keyboard = []

        for user in users:

            keyboard.append([
                InlineKeyboardButton(
                    user[1],
                    callback_data=f"unban:{user[0]}"
                )
            ])

        keyboard.append([
            InlineKeyboardButton(
                "🔙 رجوع",
                callback_data="bad"
            )
        ])

        await query.edit_message_text(
            "🚫 المحظورين",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    # =========================
    # MUTED LIST
    # =========================
    elif data == "muted":

        c.execute(
            "SELECT user_id, name FROM users WHERE muted=1"
        )

        users = c.fetchall()

        keyboard = []

        for user in users:

            keyboard.append([
                InlineKeyboardButton(
                    user[1],
                    callback_data=f"unmute:{user[0]}"
                )
            ])

        keyboard.append([
            InlineKeyboardButton(
                "🔙 رجوع",
                callback_data="bad"
            )
        ])

        await query.edit_message_text(
            "🔇 المكتومين",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    # =========================
    # USER PANEL
    # =========================
    elif data.startswith("user:"):

        uid = int(data.split(":")[1])

        u = get(uid)

        keyboard = [

            [
                InlineKeyboardButton(
                    "💰 إضافة فلوس",
                    callback_data=f"add:{uid}"
                ),

                InlineKeyboardButton(
                    "💸 خصم فلوس",
                    callback_data=f"rem:{uid}"
                )
            ],

            [
                InlineKeyboardButton(
                    "🏆 تعديل لقب",
                    callback_data=f"title:{uid}"
                )
            ],

            [
                InlineKeyboardButton(
                    "🔇 كتم",
                    callback_data=f"mute:{uid}"
                ),

                InlineKeyboardButton(
                    "🔊 فك كتم",
                    callback_data=f"unmute:{uid}"
                )
            ],

            [
                InlineKeyboardButton(
                    "🚫 حظر",
                    callback_data=f"ban:{uid}"
                ),

                InlineKeyboardButton(
                    "✅ فك حظر",
                    callback_data=f"unban:{uid}"
                )
            ],

            [
                InlineKeyboardButton(
                    "🔙 رجوع",
                    callback_data="users"
                )
            ]
        ]

        await query.edit_message_text(
f"""
👤 معلومات العضو

🆔 ID:
{u[0]}

👤 الاسم:
{u[1]}

📨 الرسائل:
{u[2]:,}

💰 المال:
{u[3]:,}

🏆 اللقب:
{u[8]}

🚫 الحظر:
{'نعم' if u[10] else 'لا'}

🔇 الكتم:
{'نعم' if u[11] else 'لا'}
""",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    # =========================
    # ADD MONEY
    # =========================
    elif data.startswith("add:"):

        uid = int(data.split(":")[1])

        set_state(
            query.from_user.id,
            "add",
            uid
        )

        await query.message.reply_text(
            "💰 أرسل المبلغ الآن"
        )

    # =========================
    # REMOVE MONEY
    # =========================
    elif data.startswith("rem:"):

        uid = int(data.split(":")[1])

        set_state(
            query.from_user.id,
            "rem",
            uid
        )

        await query.message.reply_text(
            "💸 أرسل مبلغ الخصم"
        )

    # =========================
    # TITLE
    # =========================
    elif data.startswith("title:"):

        uid = int(data.split(":")[1])

        set_state(
            query.from_user.id,
            "title",
            uid
        )

        await query.message.reply_text(
            "🏆 أرسل اللقب الجديد"
        )

    # =========================
    # MUTE
    # =========================
    elif data.startswith("mute:"):

        uid = int(data.split(":")[1])

        mute(uid)

        await query.answer(
            "🔇 تم الكتم"
        )

    # =========================
    # UNMUTE
    # =========================
    elif data.startswith("unmute:"):

        uid = int(data.split(":")[1])

        unmute(uid)

        await query.answer(
            "🔊 تم فك الكتم"
        )

    # =========================
    # BAN
    # =========================
    elif data.startswith("ban:"):

        uid = int(data.split(":")[1])

        ban(uid)

        await query.answer(
            "🚫 تم الحظر"
        )

    # =========================
    # UNBAN
    # =========================
    elif data.startswith("unban:"):

        uid = int(data.split(":")[1])

        unban(uid)

        await query.answer(
            "✅ تم فك الحظر"
        )

    # =========================
    # HOME
    # =========================
    elif data == "home":

        from core.ui import admin_menu

        await query.edit_message_text(
            "🛠 لوحة التحكم",
            reply_markup=admin_menu()
        )
