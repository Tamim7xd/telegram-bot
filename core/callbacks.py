from telegram import Update
from telegram.ext import ContextTypes

from config import ADMIN_ID, GROUP_ID
from core.ui import admin_menu, users_page, user_panel
from core.users import get
from core.actions import add_money, remove_money, set_title, mute, ban, unban
from core.state import set_state


async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    uid = query.from_user.id
    data = query.data

    if uid != ADMIN_ID:
        await query.answer("❌ غير مصرح", show_alert=True)
        return

    if data == "home":
        await query.edit_message_text("🛠 لوحة الأدمن", reply_markup=admin_menu())
        return

    if data.startswith("users:"):
        await query.edit_message_text("👥 الأعضاء", reply_markup=users_page())
        return

    if data.startswith("user:"):
        user_id = int(data.split(":")[1])
        u = get(user_id)

        if not u:
            await query.edit_message_text("❌ غير موجود")
            return

        await query.edit_message_text(
            f"👤 {u[1]}",
            reply_markup=user_panel(user_id)
        )
        return

    # ───── إدخال بيانات بعد الضغط ─────

    if data.startswith("add:"):
        set_state(uid, "add", int(data.split(":")[1]))
        await query.message.reply_text("💰 اكتب المبلغ:")
        return

    if data.startswith("rem:"):
        set_state(uid, "rem", int(data.split(":")[1]))
        await query.message.reply_text("💸 اكتب المبلغ:")
        return

    if data.startswith("title:"):
        set_state(uid, "title", int(data.split(":")[1]))
        await query.message.reply_text("🏆 اكتب اللقب:")
        return

    if data.startswith("mute:"):
        mute(int(data.split(":")[1]))
        await query.message.reply_text("🔇 تم الكتم")
        return

    if data.startswith("ban:"):
        ban(int(data.split(":")[1]))
        await query.message.reply_text("🚫 تم الحظر")
        return

    if data.startswith("unban:"):
        unban(int(data.split(":")[1]))
        await query.message.reply_text("🔓 تم فك الحظر")
        return

    if data == "close":
        await query.edit_message_text("❌ تم الإغلاق")
