import time
from telegram import Update
from telegram.ext import ContextTypes
from shared.database import get_db
from shared.permissions import is_admin
from shared.logger import log_action
from config import GROUP_ID, MAX_WARNINGS
from system_punishments.punishments_handler import ban_user

async def warning_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    admin_name = update.effective_user.first_name
    
    if not is_admin(user_id):
        await update.message.reply_text("❌ هذا الأمر للمشرفين فقط")
        return
    
    if not update.message.reply_to_message:
        await update.message.reply_text("❌ يرجى الرد على رسالة العضو المستهدف")
        return
    
    target = update.message.reply_to_message.from_user
    target_id = target.id
    target_name = target.first_name
    
    if target_id == user_id:
        await update.message.reply_text("❌ لا يمكنك تحذير نفسك")
        return
    
    text = update.message.text
    parts = text.split(maxsplit=1)
    reason = parts[1] if len(parts) > 1 else "لا يوجد سبب"
    
    conn = get_db()
    
    # إضافة تحذير
    conn.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (target_id,))
    conn.execute("UPDATE users SET warnings = warnings + 1 WHERE user_id = ?", (target_id,))
    
    cursor = conn.execute("SELECT warnings FROM users WHERE user_id = ?", (target_id,))
    warnings = cursor.fetchone()["warnings"]
    
    # تسجيل العملية
    log_action(conn, user_id, admin_name, "تحذير", target_id, target_name, reason)
    
    # إرسال إشعار
    await context.bot.send_message(
        GROUP_ID,
        f"⚠️ **تحذير**\n\n"
        f"👤 العضو: {target_name}\n"
        f"📝 السبب: {reason}\n"
        f"🔢 عدد التحذيرات: {warnings}/{MAX_WARNINGS}\n\n"
        f"👮 بواسطة: {admin_name}",
        parse_mode="Markdown"
    )
    
    # التحقق من الحد الأقصى
    if warnings >= MAX_WARNINGS:
        await ban_user(context, target_id, f"تجاوز {MAX_WARNINGS} تحذيرات")
        await context.bot.send_message(
            GROUP_ID,
            f"🚫 **تم حظر {target_name} تلقائياً**\nالسبب: تجاوز {MAX_WARNINGS} تحذيرات"
        )
    
    conn.commit()
    conn.close()