from telegram import Update
from telegram.ext import ContextTypes

from config import ADMIN_ID
from core.users import get
from core.ui import admin_menu, user_panel
from core.actions import add_money, remove_money, set_title, mute, ban, unban
from core.state import set_state


async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    q = update.callback_query
    await q.answer()

    uid = q.from_user.id
    data = q.data

    if uid != ADMIN_ID:
        return

    if data == "home":
        await q.edit_message_text("🛠 لوحة الأدمن", reply_markup=admin_menu())

    if data.startswith("user:"):
        target = int(data.split(":")[1])
        u = get(target)

        await q.edit_message_text(
            f"👤 {u[1]}",
            reply_markup=user_panel(target)
        )

    # STATE INPUT
    if data.startswith("add:"):
        set_state(uid, "add", int(data.split(":")[1]))
        await q.message.reply_text("💰 اكتب المبلغ")

    if data.startswith("rem:"):
        set_state(uid, "rem", int(data.split(":")[1]))
        await q.message.reply_text("💸 اكتب المبلغ")

    if data.startswith("title:"):
        set_state(uid, "title", int(data.split(":")[1]))
        await q.message.reply_text("🏆 اكتب اللقب")

    if data.startswith("mute:"):
        mute(int(data.split(":")[1]))
        await q.message.reply_text("🔇 تم الكتم")

    if data.startswith("ban:"):
        ban(int(data.split(":")[1]))
        await q.message.reply_text("🚫 تم الحظر")

    if data.startswith("unban:"):
        unban(int(data.split(":")[1]))
        await q.message.reply_text("🔓 تم فك الحظر")
