from telegram import Update
from telegram.ext import ContextTypes

from config import ADMIN_ID, GROUP_ID
from core.ui import admin_menu, users_page, user_panel
from core.actions import *
from core.users import get

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    q = update.callback_query
    await q.answer()

    if q.from_user.id != ADMIN_ID:
        return

    data = q.data

    # لوحة
    if data == "home":
        await q.edit_message_text("🛠 لوحة الأدمن", reply_markup=admin_menu())

    # صفحات
    elif data.startswith("users:"):
        page = int(data.split(":")[1])
        await q.edit_message_text("👥 الأعضاء", reply_markup=users_page(page))

    # عضو
    elif data.startswith("user:"):
        uid = int(data.split(":")[1])
        u = get(uid)

        await q.edit_message_text(
f"""👤 {u[1]}
💰 {u[3]}
💬 {u[2]}
🏆 {u[5]}
⚠ {u[4]}""",
            reply_markup=user_panel(uid)
        )

    # فلوس
    elif data.startswith("add:"):
        uid = int(data.split(":")[1])
        add_money(uid, 250)
        await context.bot.send_message(GROUP_ID, f"💰 تم إضافة فلوس")

    elif data.startswith("rem:"):
        uid = int(data.split(":")[1])
        remove_money(uid, 250)

    elif data.startswith("title:"):
        set_title(int(data.split(":")[1]), "أسطورة")

    elif data.startswith("mute:"):
        mute(int(data.split(":")[1]))

    elif data.startswith("ban:"):
        ban(int(data.split(":")[1]))

    elif data.startswith("unban:"):
        unban(int(data.split(":")[1]))
