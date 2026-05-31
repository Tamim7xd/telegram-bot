from telegram import Update
from telegram.ext import ContextTypes
from shared.database import get_db
from shared.permissions import is_admin, is_super_admin
from config import GROUP_ID
from system_punishments.punishments_handler import ban_user
from .warnings_data import MAX_WARNINGS, AUTO_BAN_ON_MAX

async def warning_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.message.reply_text("❌ هذا الأمر للمشرفين فقط")
        return
    
    if not update.message.reply_to_message:
        await update.message.reply_text("❌ يرجى الرد على رسالة العضو الذي تريد تحذيره")
        return
    
    target_user = update.message.reply_to_message.from_user
    target_id = target_user.id
    
    if target_id == user_id:
        await update.message.reply_text("❌ لا يمكنك تحذير نفسك")
        return
    
    # استخراج السبب
    text = update.message.text
    parts = text.split(maxsplit=1)
    reason = parts[1] if len(parts) > 1 else "لا يوجد سبب"
    
    conn = get_db()
    
    # إضافة تحذير
    conn.execute("UPDATE users SET warnings = warnings + 1 WHERE user_id = ?", (target_id,))
    cursor = conn.execute("SELECT warnings FROM users WHERE user_id = ?", (target_id,))
    result = cursor.fetchone()
    
    if not result:
        conn.execute("INSERT INTO users (user_id) VALUES (?)", (target_id,))
        warnings = 1
    else:
        warnings = result["warnings"] + 1
        if result["warnings"] == 0:
            warnings = 1
    
    # تسجيل العملية
    import time
    conn.execute(
        "INSERT INTO logs (admin_id, action, target_id, reason, timestamp) VALUES (?, ?, ?, ?, ?)",
        (user_id, "تحذير", target_id, reason, int(time.time()))
    )
    conn.commit()
    
    # إرسال إشعار
    await context.bot.send_message(
        GROUP_ID,
        f"⚠️ **تحذير**\n\n"
        f"👤 العضو: {target_user.first_name}\n"
        f"📝 السبب: {reason}\n"
        f"🔢 عدد التحذيرات: {warnings}/{MAX_WARNINGS}\n\n"
        f"👮 بواسطة: {update.effective_user.first_name}",
        parse_mode="Markdown"
    )
    
    # التحقق من الحد الأقصى
    if AUTO_BAN_ON_MAX and warnings >= MAX_WARNINGS:
        await ban_user(context, target_id, f"تجاوز الحد الأقصى للتحذيرات ({MAX_WARNINGS})")
        await context.bot.send_message(
            GROUP_ID,
            f"🚫 **تم حظر {target_user.first_name} تلقائياً**\nسبب: تجاوز {MAX_WARNINGS} تحذيرات"
        )
    
    conn.close()