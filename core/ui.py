from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from db import c

def admin_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("👥 الأعضاء", callback_data="users:0")],
        [InlineKeyboardButton("📊 الإحصائيات", callback_data="stats")],
        [InlineKeyboardButton("📢 إرسال", callback_data="send")],
        [InlineKeyboardButton("🚫 مخالفات", callback_data="punish")],
        [InlineKeyboardButton("❌ إغلاق", callback_data="close")]
    ])


def users_page(page=0):
    limit = 5
    offset = page * limit

    c.execute("SELECT user_id,name FROM users LIMIT ? OFFSET ?", (limit, offset))
    users = c.fetchall()

    buttons = []

    for u in users:
        buttons.append([
            InlineKeyboardButton(u[1], callback_data=f"user:{u[0]}")
        ])

    nav = []

    if page > 0:
        nav.append(InlineKeyboardButton("⬅", callback_data=f"users:{page-1}"))

    nav.append(InlineKeyboardButton("➡", callback_data=f"users:{page+1}"))

    buttons.append(nav)
    buttons.append([InlineKeyboardButton("🔙 رجوع", callback_data="home")])

    return InlineKeyboardMarkup(buttons)


def user_panel(uid):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💰 فلوس", callback_data=f"add:{uid}")],
        [InlineKeyboardButton("➖ خصم", callback_data=f"rem:{uid}")],
        [InlineKeyboardButton("🏆 لقب", callback_data=f"title:{uid}")],
        [InlineKeyboardButton("🔇 كتم", callback_data=f"mute:{uid}")],
        [InlineKeyboardButton("🚫 حظر", callback_data=f"ban:{uid}")],
        [InlineKeyboardButton("🔓 فك", callback_data=f"unban:{uid}")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="users:0")]
    ])
