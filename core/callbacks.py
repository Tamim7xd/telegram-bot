from telegram import Update
from telegram.ext import ContextTypes

from config import ADMIN_ID, GROUP_ID
from core.ui import admin_menu, users_page, user_panel
from core.users import get
from core.actions import add_money, remove_money, set_title, mute, ban, unban


# ─────────────────────────────
# 🎛 CALLBACK HANDLER
# ─────────────────────────────
async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    data = query.data

    # ───────── حماية الأدمن ─────────
    if user_id != ADMIN_ID:
        await query.answer("❌ غير مصرح", show_alert=True)
        return

    # ───────── الرجوع ─────────
    if data == "home":
        await query.edit_message_text(
            "🛠 لوحة الأدمن",
            reply_markup=admin_menu()
        )
        return

    # ───────── الأعضاء (Pagination) ─────────
    if data.startswith("users:"):

        page = int(data.split(":")[1])

        await query.edit_message_text(
            "👥 قائمة الأعضاء",
            reply_markup=users_page(page)
        )
        return

    # ───────── فتح مستخدم ─────────
    if data.startswith("user:"):

        uid = int(data.split(":")[1])
        u = get(uid)

        if not u:
            await query.edit_message_text("❌ المستخدم غير موجود")
            return

        await query.edit_message_text(
f"""👤 ملف المستخدم

🆔 ID: {u[0]}
👤 الاسم: {u[1]}
💰 فلوس: {u[3]}
⭐ XP: {u[4]}
📊 مستوى: {u[5]}
⚠ تنبيهات: {u[6]}
🏆 لقب: {u[7]}

🚫 حالة:
{'محظور' if len(u) > 8 and u[8] else 'نشط'}
""",
            reply_markup=user_panel(uid)
        )
        return

    # ───────── إضافة فلوس ─────────
    if data.startswith("add:"):

        uid = int(data.split(":")[1])
        add_money(uid, 250)

        await context.bot.send_message(
            GROUP_ID,
            f"💰 تم إضافة 250 دينار للمستخدم {uid} بواسطة الأدمن"
        )

        await query.answer("تمت الإضافة", show_alert=True)
        return

    # ───────── خصم ─────────
    if data.startswith("rem:"):

        uid = int(data.split(":")[1])
        remove_money(uid, 250)

        await context.bot.send_message(
            GROUP_ID,
            f"💸 تم خصم 250 دينار من المستخدم {uid}"
        )

        await query.answer("تم الخصم", show_alert=True)
        return

    # ───────── لقب ─────────
    if data.startswith("title:"):

        uid = int(data.split(":")[1])
        set_title(uid, "أسطورة")

        await context.bot.send_message(
            GROUP_ID,
            f"🏆 تم تعديل لقب المستخدم {uid}"
        )

        await query.answer("تم تعديل اللقب", show_alert=True)
        return

    # ───────── كتم ─────────
    if data.startswith("mute:"):

        uid = int(data.split(":")[1])
        mute(uid)

        await context.bot.send_message(
            GROUP_ID,
            f"🔇 تم كتم المستخدم {uid}"
        )

        await query.answer("تم الكتم", show_alert=True)
        return

    # ───────── حظر ─────────
    if data.startswith("ban:"):

        uid = int(data.split(":")[1])
        ban(uid)

        await context.bot.send_message(
            GROUP_ID,
            f"🚫 تم حظر المستخدم {uid}"
        )

        await query.answer("تم الحظر", show_alert=True)
        return

    # ───────── فك حظر ─────────
    if data.startswith("unban:"):

        uid = int(data.split(":")[1])
        unban(uid)

        await context.bot.send_message(
            GROUP_ID,
            f"🔓 تم فك حظر المستخدم {uid}"
        )

        await query.answer("تم فك الحظر", show_alert=True)
        return

    # ───────── إغلاق ─────────
    if data == "close":
        await query.edit_message_text("❌ تم إغلاق اللوحة")
        return
