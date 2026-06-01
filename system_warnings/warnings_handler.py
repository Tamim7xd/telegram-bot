import time
from telegram import Update
from telegram.ext import ContextTypes
from shared.database import get_db
from shared.permissions import is_admin
from shared.logger import log_action
from config import GROUP_ID, MAX_WARNINGS

async def warning_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    admin_name = update.effective_user.first_name
    
    if not is_admin(user_id):
        await update.message.reply_text("❌ هذا الأمر للمشرفين فقط")
        return
    
    if not update.message.reply_to_message:
        await update.message.reply_text("❌ يرجى الرد على رسالة العضو")
        return
    
    target = update.message.reply_to_message.from_user
    target_id = target.id
    target_name = target.first_name
    
    text = update.message.text
    parts = text.split(maxsplit=1)
    reason = parts[1] if len(parts) > 1 else "لا يوجد سبب"
    
    conn = get_db()
    conn.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (target_id,))
    conn.execute("UPDATE users SET warnings = warnings + 1 WHERE user_id = ?", (target_id,))
    
    cursor = conn.execute("SELECT warnings FROM users WHERE user_id = ?", (target_id,))
    warnings = cursor.fetchone()["warnings"]
    
    log_action(conn, user_id, admin_name, "تحذير", target_id, target_name, reason)
    
    await context.bot.send_message(GROUP_ID, f"⚠️ **تحذير**\n\n👤 {target_name}\n📝 {reason}\n🔢 {warnings}/{MAX_WARNINGS}\n\n👮 بواسطة: {admin_name}", parse_mode="Markdown")
    
    if warnings >= MAX_WARNINGS:
        try:
            await context.bot.ban_chat_member(GROUP_ID, target_id)
            await context.bot.send_message(GROUP_ID, f"🚫 **تم حظر {target_name} تلقائياً**\nالسبب: تجاوز {MAX_WARNINGS} تحذيرات")
        except:
            pass
    
    conn.commit()
    conn.close()