from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from db import c
from core.service import get_user, is_admin

ADMIN_ID = 1007010982


def admin_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("👥 المستخدمين", callback_data="admin_users")],
        [InlineKeyboardButton("📊 الإحصائيات", callback_data="admin_stats")],
        [InlineKeyboardButton("🏆 الترتيب", callback_data="admin_top")]
    ])


async def callback_handler(update, context):

    query = update.callback_query
    await query.answer()

    data = query.data

    if not is_admin(query.from_user.id):
        return

    if data == "admin":

        await query.edit_message_text("🛠 لوحة الأدمن", reply_markup=admin_menu())

    elif data == "admin_users":

        c.execute("SELECT user_id, name FROM users LIMIT 20")
        users = c.fetchall()

        keyboard = [
            [InlineKeyboardButton(u[1], callback_data=f"user:{u[0]}")]
            for u in users
        ]

        await query.edit_message_text("👥 المستخدمين", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data.startswith("user:"):

        uid = int(data.split(":")[1])
        u = get_user(uid)

        await query.edit_message_text(f"""
👤 {u[1]}
💰 {u[3]}
⭐ {u[5]}
🔥 {u[4]}
🏆 {u[6]}
""")

    elif data == "admin_stats":

        c.execute("SELECT COUNT(*) FROM users")
        users = c.fetchone()[0]

        await query.edit_message_text(f"👥 {users} مستخدم")
