from telegram import (
    Update,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ChatPermissions
)

from telegram.ext import ContextTypes

from config import ADMIN_ID, GROUP_ID
from db import c, conn

from core.users import get
from core.state import set_state
from core.actions import (
    add_money,
    remove_money,
    set_title,
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
        await query.answer("❌ ليس لديك صلاحية", show_alert=True)
        return

    # =========================
    # HOME
    # =========================
    if data == "home":

        from core.ui import admin_menu

        await query.edit_message_text(
            "🛠 لوحة التحكم",
            reply_markup=admin_menu()
        )

    # =========================
    # USERS LIST
    # =========================
    elif data == "users":

        c.execute("SELECT user_id, name FROM users LIMIT 20")
        users = c.fetchall()

        keyboard = []

        for u in users:
            keyboard.append([
                InlineKeyboardButton(
                    u[1],
                    callback_data=f"user:{u[0]}"
                )
            ])

        keyboard.append([
            InlineKeyboardButton("🔙 رجوع", callback_data="home")
        ])

        await query.edit_message_text(
            "👥 قائمة الأعضاء",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    # =========================
    # USER PROFILE
    # =========================
    elif data.startswith("user:"):

        uid = int(data.split(":")[1])
        u = get(uid)

        keyboard = [

            [
                InlineKeyboardButton("💰 إضافة", callback_data=f"add:{uid}"),
                InlineKeyboardButton("💸 خصم", callback_data=f"rem:{uid}")
            ],

            [
                InlineKeyboardButton("🏆 لقب", callback_data=f"title:{uid}")
            ],

            [
                InlineKeyboardButton("🔇 كتم", callback_data=f"mute:{uid}"),
                InlineKeyboardButton("🔊 فك", callback_data=f"unmute:{uid}")
            ],

            [
                InlineKeyboardButton("🚫 حظر", callback_data=f"ban:{uid}"),
                InlineKeyboardButton("✅ فك", callback_data=f"unban:{uid}")
            ],

            [
                InlineKeyboardButton("👢 طرد", callback_data=f"kick:{uid}")
            ],

            [
                InlineKeyboardButton("🔙 رجوع", callback_data="users")
            ]
        ]

        await query.edit_message_text(
f"""
👤 معلومات العضو

🆔 {u[0]}
👤 {u[1]}
💰 المال: {u[3]:,}
📨 الرسائل: {u[2]:,}
🏆 اللقب: {u[8]}

🚫 محظور: {'نعم' if u[10] else 'لا'}
🔇 مكتوم: {'نعم' if u[11] else 'لا'}
""",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    # =========================
    # ADD MONEY (STATE)
    # =========================
    elif data.startswith("add:"):
        uid = int(data.split(":")[1])
        set_state(query.from_user.id, "add", uid)
        await query.message.reply_text("💰 أرسل المبلغ")

    # =========================
    # REMOVE MONEY
    # =========================
    elif data.startswith("rem:"):
        uid = int(data.split(":")[1])
        set_state(query.from_user.id, "rem", uid)
        await query.message.reply_text("💸 أرسل مبلغ الخصم")

    # =========================
    # TITLE
    # =========================
    elif data.startswith("title:"):
        uid = int(data.split(":")[1])
        set_state(query.from_user.id, "title", uid)
        await query.message.reply_text("🏆 أرسل اللقب")

    # =========================
    # MUTE
    # =========================
    elif data.startswith("mute:"):

        uid = int(data.split(":")[1])

        await context.bot.restrict_chat_member(
            GROUP_ID,
            uid,
            permissions=ChatPermissions(
                can_send_messages=False
            )
        )

        c.execute("UPDATE users SET muted=1 WHERE user_id=?", (uid,))
        conn.commit()

        await context.bot.send_message(
            GROUP_ID,
f"""
🔇 تم كتم العضو
بواسطة: {query.from_user.first_name}
"""
        )

    # =========================
    # UNMUTE
    # =========================
    elif data.startswith("unmute:"):

        uid = int(data.split(":")[1])

        await context.bot.restrict_chat_member(
            GROUP_ID,
            uid,
            permissions=ChatPermissions(
                can_send_messages=True,
                can_send_media_messages=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True
            )
        )

        c.execute("UPDATE users SET muted=0 WHERE user_id=?", (uid,))
        conn.commit()

        await query.answer("🔊 تم فك الكتم")

    # =========================
    # BAN
    # =========================
    elif data.startswith("ban:"):

        uid = int(data.split(":")[1])

        await context.bot.ban_chat_member(GROUP_ID, uid)

        c.execute("UPDATE users SET banned=1 WHERE user_id=?", (uid,))
        conn.commit()

        await context.bot.send_message(
            GROUP_ID,
f"""
🚫 تم حظر العضو
بواسطة: {query.from_user.first_name}
"""
        )

    # =========================
    # UNBAN
    # =========================
    elif data.startswith("unban:"):

        uid = int(data.split(":")[1])

        await context.bot.unban_chat_member(GROUP_ID, uid)

        c.execute("UPDATE users SET banned=0 WHERE user_id=?", (uid,))
        conn.commit()

        await query.answer("✅ تم فك الحظر")

    # =========================
    # KICK
    # =========================
    elif data.startswith("kick:"):

        uid = int(data.split(":")[1])

        await context.bot.ban_chat_member(GROUP_ID, uid)
        await context.bot.unban_chat_member(GROUP_ID, uid)

        await context.bot.send_message(
            GROUP_ID,
f"""
👢 تم طرد العضو
بواسطة: {query.from_user.first_name}
"""
        )

        await query.answer("👢 تم الطرد")

    # =========================
    # STATS
    # =========================
    elif data == "stats":

        c.execute("SELECT COUNT(*) FROM users")
        users = c.fetchone()[0]

        c.execute("SELECT SUM(messages) FROM users")
        messages = c.fetchone()[0] or 0

        c.execute("SELECT SUM(money) FROM users")
        money = c.fetchone()[0] or 0

        c.execute("SELECT COUNT(*) FROM users WHERE banned=1")
        banned = c.fetchone()[0]

        c.execute("SELECT COUNT(*) FROM users WHERE muted=1")
        muted = c.fetchone()[0]

        await query.edit_message_text(
f"""
📊 الإحصائيات

👥 الأعضاء: {users}
📨 الرسائل: {messages}
💰 الأموال: {money}

🚫 محظورين: {banned}
🔇 مكتومين: {muted}
"""
        )
