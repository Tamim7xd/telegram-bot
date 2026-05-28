from telegram import Update
from telegram.ext import ContextTypes

from config import ADMIN_ID

from core.state import set_state


# =========================
# CALLBACK HANDLER
# =========================
async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    await query.answer()

    data = query.data

    if query.from_user.id != ADMIN_ID:
        return

    # =========================
    # CLOSE
    # =========================
    if data == "close":

        await query.edit_message_text(
            "❌ تم إغلاق اللوحة"
        )

    # =========================
    # USER PANEL
    # =========================
    elif data.startswith("user:"):

        uid = int(data.split(":")[1])

        await query.edit_message_text(
f"""
👤 لوحة العضو

🆔 {uid}

اختر العملية:

➕ إضافة فلوس
➖ خصم فلوس
🏆 تعديل لقب
🔇 كتم
🚫 حظر
"""
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
