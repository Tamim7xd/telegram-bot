from telegram import Update
from telegram.ext import ContextTypes

from config import ADMIN_ID, GROUP_ID

from core.ui import admin_menu, users_page, user_panel
from core.users import get
from core.actions import add_money, remove_money, set_title, mute, ban, unban

# ─────────────────────────────
# 🎛️ CALLBACK HANDLER
# ─────────────────────────────
async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    data = query.data

    # ───── حماية الأدمن ─────
    if user_id != ADMIN_ID:
        await query.edit_message_text("❌ غير مصرح لك")
        return

    # ───── الرجوع للوحة ─────
    if data == "home":
        await query.edit_message_text(
            "🛠 لوحة الأدمن",
            reply_markup=admin_menu()
        )

    # ───── قائمة الأعضاء (pagination) ─────
    elif data.startswith("users:"):
        try:
            page = int(data.split(":")[1])
        except:
            page = 0

        await query.edit_message_text(
            "👥 قائمة الأعضاء",
            reply_markup=users_page(page)
        )

    # ───── فتح ملف عضو ─────
    elif data.startswith("user:"):
        uid = int(data.split(":")[1])
        u = get(uid)

        if not u:
            await query.edit_message_text("❌ المستخدم غير موجود")
            return

        await query.edit_message_text(
f"""👤 ━━━ ملف المستخدم ━━━

🆔 ID: {u[0]}
👤 الاسم: {u[1]}
💰 الفلوس: {u[2]}
⭐ XP: {u[3]}
📊 المستوى: {u[4]}
🏆 اللقب: {u[6]}
⚠ التنبيهات: {u[5]}
🚫 الحالة: {"محظور" if u[7] else "نشط"}

━━━━━━━━━━━━━━""",
            reply_markup=user_panel(uid)
        )

    # ─────────────────────────────
    # 💰 إضافة فلوس
    # ─────────────────────────────
    elif data.startswith("add:"):
        uid = int(data.split(":")[1])

        add_money(uid, 250)

        await context.bot.send_message(
            GROUP_ID,
f"""💰 ━━━ عملية مالية ━━━

👤 تم إضافة فلوس
💵 المبلغ: 250 دينار
👮 بواسطة: ADMIN

━━━━━━━━━━━━━━"""
        )

        await query.answer("تم إضافة الفلوس")

    # ─────────────────────────────
    # ➖ خصم فلوس
    # ─────────────────────────────
    elif data.startswith("rem:"):
        uid = int(data.split(":")[1])

        remove_money(uid, 250)

        await context.bot.send_message(
            GROUP_ID,
f"""💸 ━━━ عملية مالية ━━━

👤 تم خصم فلوس
💵 المبلغ: 250 دينار
👮 بواسطة: ADMIN

━━━━━━━━━━━━━━"""
        )

        await query.answer("تم الخصم")

    # ─────────────────────────────
    # 🏆 تعديل لقب
    # ─────────────────────────────
    elif data.startswith("title:"):
        uid = int(data.split(":")[1])

        set_title(uid, "أسطورة")

        await context.bot.send_message(
            GROUP_ID,
f"""🏆 ━━━ ترقية لقب ━━━

👤 تم تعديل اللقب
✨ اللقب الجديد: أسطورة

👮 بواسطة: ADMIN

━━━━━━━━━━━━━━"""
        )

        await query.answer("تم تعديل اللقب")

    # ─────────────────────────────
    # 🔇 كتم
    # ─────────────────────────────
    elif data.startswith("mute:"):
        uid = int(data.split(":")[1])

        mute(uid)

        await context.bot.send_message(
            GROUP_ID,
f"""🔇 ━━━ إجراء إداري ━━━

👤 تم كتم المستخدم
⏱ الحالة: MUTE

👮 بواسطة: ADMIN

━━━━━━━━━━━━━━"""
        )

        await query.answer("تم الكتم")

    # ─────────────────────────────
    # 🚫 حظر
    # ─────────────────────────────
    elif data.startswith("ban:"):
        uid = int(data.split(":")[1])

        ban(uid)

        await context.bot.send_message(
            GROUP_ID,
f"""🚫 ━━━ إجراء إداري ━━━

👤 تم حظر المستخدم
⚠️ الحالة: BAN

👮 بواسطة: ADMIN

━━━━━━━━━━━━━━"""
        )

        await query.answer("تم الحظر")

    # ─────────────────────────────
    # 🔓 فك الحظر
    # ─────────────────────────────
    elif data.startswith("unban:"):
        uid = int(data.split(":")[1])

        unban(uid)

        await context.bot.send_message(
            GROUP_ID,
f"""🔓 ━━━ إجراء إداري ━━━

👤 تم فك الحظر

👮 بواسطة: ADMIN

━━━━━━━━━━━━━━"""
        )

        await query.answer("تم فك الحظر")

    # ─────────────────────────────
    # ❌ إغلاق
    # ─────────────────────────────
    elif data == "close":
        await query.edit_message_text("❌ تم إغلاق اللوحة")
