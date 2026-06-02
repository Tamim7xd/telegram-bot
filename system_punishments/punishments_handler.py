import time
import re
import asyncio
import telegram
from telegram import Update
from telegram.ext import ContextTypes
from shared.database import get_db
from shared.permissions import is_admin, is_super_admin
from shared.logger import log_action
from config import GROUP_ID

# دوال تحويل الوقت
def parse_duration(duration_str):
    if not duration_str:
        return 600
    duration_str = duration_str.strip()
    if duration_str.endswith('د'):
        try:
            num = int(duration_str[:-1])
            return num * 60
        except:
            pass
    if duration_str.endswith('س'):
        try:
            num = int(duration_str[:-1])
            return num * 3600
        except:
            pass
    if duration_str == 'يوم':
        return 86400
    try:
        num = int(duration_str)
        return num * 60
    except:
        pass
    return 600

def format_duration(seconds):
    if seconds >= 86400:
        return f"{seconds // 86400} يوم"
    elif seconds >= 3600:
        return f"{seconds // 3600} ساعة"
    elif seconds >= 60:
        return f"{seconds // 60} دقيقة"
    else:
        return f"{seconds} ثانية"

DEFAULT_MUTE_DURATION = 600

async def mute_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    target_username = target.username or "لا يوجد"
    
    text = update.message.text
    parts = text.split(maxsplit=2)
    
    duration_seconds = DEFAULT_MUTE_DURATION
    duration_str = ""
    reason = ""
    
    if len(parts) >= 2:
        time_part = parts[1]
        time_patterns = [r'^\d+د$', r'^\d+س$', r'^يوم$']
        is_time = False
        for pattern in time_patterns:
            if re.match(pattern, time_part):
                is_time = True
                break
        
        if is_time:
            duration_seconds = parse_duration(time_part)
            duration_str = time_part
            reason = parts[2] if len(parts) > 2 else "لا يوجد سبب"
        else:
            reason = time_part
            duration_str = "10د"
            duration_seconds = 600
    
    if not reason:
        reason = "لا يوجد سبب"
    
    if not duration_str:
        duration_str = format_duration(duration_seconds)
    
    until_time = int(time.time()) + duration_seconds
    
    try:
        await context.bot.restrict_chat_member(
            GROUP_ID, 
            target_id, 
            permissions=telegram.ChatPermissions(can_send_messages=False)
        )
    except Exception as e:
        print(f"Mute error: {e}")
    
    conn = get_db()
    conn.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (target_id,))
    conn.execute("UPDATE users SET is_muted = 1, muted_until = ? WHERE user_id = ?", (until_time, target_id))
    log_action(conn, user_id, admin_name, "كتم", target_id, target_name, reason)
    conn.commit()
    conn.close()
    
    await context.bot.send_message(
        GROUP_ID,
        f"🔇 **كتم**\n\n"
        f"👤 العضو: {target_name} (@{target_username})\n"
        f"⏱️ المدة: {duration_str}\n"
        f"📝 السبب: {reason}\n\n"
        f"👮 بواسطة: {admin_name}"
    )

async def ban_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    admin_name = update.effective_user.first_name
    
    if not is_super_admin(user_id):
        await update.message.reply_text("❌ هذا الأمر للمشرف الإداري فقط")
        return
    
    if not update.message.reply_to_message:
        await update.message.reply_text("❌ يرجى الرد على رسالة العضو المستهدف")
        return
    
    target = update.message.reply_to_message.from_user
    target_id = target.id
    target_name = target.first_name
    target_username = target.username or "لا يوجد"
    
    text = update.message.text
    parts = text.split(maxsplit=1)
    reason = parts[1] if len(parts) > 1 else "لا يوجد سبب"
    
    try:
        await context.bot.ban_chat_member(GROUP_ID, target_id)
    except Exception as e:
        print(f"Ban error: {e}")
    
    conn = get_db()
    conn.execute("UPDATE users SET is_banned = 1 WHERE user_id = ?", (target_id,))
    log_action(conn, user_id, admin_name, "حظر", target_id, target_name, reason)
    conn.commit()
    conn.close()
    
    await context.bot.send_message(
        GROUP_ID,
        f"🚫 **حظر**\n\n"
        f"👤 العضو: {target_name} (@{target_username})\n"
        f"📝 السبب: {reason}\n\n"
        f"👮 بواسطة: {admin_name}"
    )

async def kick_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    admin_name = update.effective_user.first_name
    
    if not is_super_admin(user_id):
        await update.message.reply_text("❌ هذا الأمر للمشرف الإداري فقط")
        return
    
    if not update.message.reply_to_message:
        await update.message.reply_text("❌ يرجى الرد على رسالة العضو المستهدف")
        return
    
    target = update.message.reply_to_message.from_user
    target_id = target.id
    target_name = target.first_name
    target_username = target.username or "لا يوجد"
    
    text = update.message.text
    parts = text.split(maxsplit=1)
    reason = parts[1] if len(parts) > 1 else "لا يوجد سبب"
    
    try:
        await context.bot.ban_chat_member(GROUP_ID, target_id)
        await context.bot.unban_chat_member(GROUP_ID, target_id)
    except Exception as e:
        print(f"Kick error: {e}")
    
    conn = get_db()
    log_action(conn, user_id, admin_name, "طرد", target_id, target_name, reason)
    conn.commit()
    conn.close()
    
    await context.bot.send_message(
        GROUP_ID,
        f"👢 **طرد**\n\n"
        f"👤 العضو: {target_name} (@{target_username})\n"
        f"📝 السبب: {reason}\n\n"
        f"👮 بواسطة: {admin_name}"
    )

async def unmute_user(context, user_id, send_notification=True):
    """فك الكتم عن عضو وتحديث قاعدة البيانات"""
    try:
        await context.bot.restrict_chat_member(
            GROUP_ID, 
            user_id, 
            permissions=telegram.ChatPermissions(
                can_send_messages=True,
                can_send_media_messages=True,
                can_send_other_messages=True
            )
        )
    except Exception as e:
        print(f"Unmute error: {e}")
    
    conn = get_db()
    conn.execute("UPDATE users SET is_muted = 0, muted_until = 0 WHERE user_id = ?", (user_id,))
    conn.commit()
    
    # جلب اسم العضو للإشعار
    cursor = conn.execute("SELECT first_name, username FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    
    if send_notification and user:
        name = user["first_name"] or user["username"] or str(user_id)
        username = user["username"] or "لا يوجد"
        await context.bot.send_message(
            GROUP_ID,
            f"🔓 **تم فك الكتم**\n\n"
            f"👤 العضو: {name} (@{username})\n"
            f"✅ يمكنه التحدث مرة أخرى"
        )
    
    return user if user else None

async def check_expired_mutes(context):
    """فحص الأعضاء الذين انتهت مدتهم وفك الكتم عنهم"""
    conn = get_db()
    current_time = int(time.time())
    
    cursor = conn.execute("SELECT user_id FROM users WHERE is_muted = 1 AND muted_until <= ?", (current_time,))
    expired_users = cursor.fetchall()
    
    for user in expired_users:
        user_id = user["user_id"]
        await unmute_user(context, user_id, send_notification=True)
    
    conn.close()