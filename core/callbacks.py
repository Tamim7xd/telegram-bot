from telegram import Update
from telegram.ext import ContextTypes

from config import ADMIN_ID, GROUP_ID

from core.ui import admin_menu, users_page, user_panel
from core.users import get
from core.actions import add_money, remove_money, set_title, mute, ban, unban


# ─────────────────────────────
# 🎛️ CALLBACK HANDLER (LIVE SYSTEM)
# ─────────────────────────────
async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    data = query.data
    admin = query.from_user.id

    # ───────── حماية الأدمن ─────────
    if admin != ADMIN_ID:
        await query.answer("❌ غير مصرح", show_alert=True)
        return

    # ───────── الرجوع للوحة ─────────
    if data == "home":
        await query.edit_message_text(
            "🛠 لوحة الأدمن",
            reply_markup=admin_menu()
        )
        return

    # ───────── صفحة الأعضاء ─────────
    if data.startswith("users:"):

        try:
            page = int(data.split(":")[1])
        except:
            page = 0

        await query.edit_message_text(
            "👥 الأعضاء",
            reply_markup=users_page(page)
        )
        return

    # ───────── ملف المستخدم ─────────
    if data.startswith("user:"):

        uid = int(data.split(":")[1])
        u = get(uid)

        if not u:
            await query.edit_message_text("❌ المستخدم غير موجود")
            return

        await query.edit_message_text(
f"""👤 ━━━ ملف العضو ━━━

🆔 {u[0]}
👤 {u[1]}
💰 فلوس: {u[2]}
⭐ XP: {u[3]}
📊 مستوى: {u[4]}
🏆 لقب: {u[6]}
⚠ تنبيهات: {u[5]}
🚫 حالة: {"محظور" if u[7] else "نشط"}

━━━━━━━━━━━━""",
            reply_markup=user_panel(uid)
        )
        return

    # ─────────────────────────────
    # 💰 إضافة فلوس (حقيقي)
    # ─────────────────────────────
    if data.startswith("add:"):

        uid = int(data.split(":")[1])

        add_money(uid, 250)

        user = get(uid)

        await context.bot.send_message(
            GROUP_ID,
f"""💰 ━━━ عملية مالية ━━━

👤 المستخدم: {user[1]}
➕ تمت إضافة: 250 دينار
💰 الرصيد الجديد: {user[2]}

👮 بواسطة: ADMIN

━━━━━━━━━━━━"""
        )

        await query.answer("تمت إضافة الفلوس")
        return

    # ─────────────────────────────
    # ➖ خصم فلوس (حقيقي)
    # ─────────────────────────────
    if data.startswith("rem:"):

        uid = int(data.split(":")[1])

        remove_money(uid, 250)

        user = get(uid)

        await context.bot.send_message(
            GROUP_ID,
f"""💸 ━━━ عملية مالية ━━━

👤 المستخدم: {user[1]}
➖ تم خصم: 250 دينار
💰 الرصيد الجديد: {user[2]}

👮 بواسطة: ADMIN

━━━━━━━━━━━━"""
        )

        await query.answer("تم الخصم")
        return

    # ─────────────────────────────
    # 🏆 تعديل لقب (حقيقي)
    # ─────────────────────────────
    if data.startswith("title:"):

        uid = int(data.split(":")[1])

        set_title(uid, "أسطورة")

        user = get(uid)

        await context.bot.send_message(
            GROUP_ID,
f"""🏆 ━━━ ترقية لقب ━━━

👤 المستخدم: {user[1]}
✨ اللقب الجديد: أسطورة

👮 بواسطة: ADMIN

━━━━━━━━━━━━"""
        )

        await query.answer("تم تعديل اللقب")
        return

    # ─────────────────────────────
    # 🔇 كتم (حقيقي)
    # ─────────────────────────────
    if data.startswith("mute:"):

        uid = int(data.split(":")[1])

        mute(uid)

        user = get(uid)

        await context.bot.send_message(
            GROUP_ID,
f"""🔇 ━━━ كتم ━━━

👤 المستخدم: {user[1]}
⚠ تم كتمه من النظام

👮 بواسطة: ADMIN

━━━━━━━━━━━━"""
        )

        await query.answer("تم الكتم")
        return

    # ─────────────────────────────
    # 🚫 حظر (حقيقي)
    # ─────────────────────────────
    if data.startswith("ban:"):

        uid = int(data.split(":")[1])

        ban(uid)

        user = get(uid)

        await context.bot.send_message(
            GROUP_ID,
f"""🚫 ━━━ حظر ━━━

👤 المستخدم: {user[1]}
❌ تم حظره نهائيًا

👮 بواسطة: ADMIN

━━━━━━━━━━━━"""
        )

        await query.answer("تم الحظر")
        return

    # ─────────────────────────────
    # 🔓 فك الحظر
    # ─────────────────────────────
    if data.startswith("unban:"):

        uid = int(data.split(":")[1])

        unban(uid)

        user = get(uid)

        await context.bot.send_message(
            GROUP_ID,
f"""🔓 ━━━ فك الحظر ━━━

👤 المستخدم: {user[1]}
✅ تم إعادة تفعيله

👮 بواسطة: مصطفى،التميمي

━━━━━━━━━━━━"""
        )

        await query.answer("تم فك الحظر")
        return

    # ─────────────────────────────
    # ❌ إغلاق
    # ─────────────────────────────
    if data == "close":
        await query.edit_message_text("❌ تم إغلاق لوحة التحكم")
        return
