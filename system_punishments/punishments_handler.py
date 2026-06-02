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

def parse_duration(duration_str):
    """تحويل النص إلى ثواني - يدعم: ث، د، س، ساعة، ساعات، يوم"""
    if not duration_str:
        return 600
    
    duration_str = duration_str.strip()
    
    # ثواني (مثال: 30ث، 45ثانية)
    if duration_str.endswith('ث'):
        try:
            num = int(duration_str[:-1])
            return num
        except:
            pass
    if duration_str.endswith('ثانية'):
        try:
            num = int(duration_str.replace('ثانية', ''))
            return num
        except:
            pass
    if duration_str.endswith('ثواني'):
        try:
            num = int(duration_str.replace('ثواني', ''))
            return num
        except:
            pass
    
    # دقائق (مثال: 1د، 5دقيقة، 10دقائق)
    if duration_str.endswith('د'):
        try:
            num = int(duration_str[:-1])
            return num * 60
        except:
            pass
    if duration_str.endswith('دقيقة'):
        try:
            num = int(duration_str.replace('دقيقة', ''))
            return num * 60
        except:
            pass
    if duration_str.endswith('دقائق'):
        try:
            num = int(duration_str.replace('دقائق', ''))
            return num * 60
        except:
            pass
    
    # ساعات (مثال: 1س، 2ساعة، 3ساعات)
    if duration_str.endswith('س'):
        try:
            num = int(duration_str[:-1])
            return num * 3600
        except:
            pass
    if duration_str.endswith('ساعة'):
        try:
            num = int(duration_str.replace('ساعة', ''))
            return num * 3600
        except:
            pass
    if duration_str.endswith('ساعات'):
        try:
            num = int(duration_str.replace('ساعات', ''))
            return num * 3600
        except:
            pass
    
    # أيام
    if duration_str == 'يوم':
        return 86400
    
    # رقم فقط (يعتبر دقائق)
    try:
        num = int(duration_str)
        return num * 60
    except:
        pass
    
    return 600  # افتراضي 10 دقائق

def format_duration(seconds):
    """تحويل الثواني إلى نص مفهوم"""
    if seconds >= 86400:
        days = seconds // 86400
        return f"{days} يوم" + ("ين" if days == 2 else "")
    elif seconds >= 3600:
        hours = seconds // 3600
        return f"{hours} ساعة" + ("ات" if hours >= 3 else ("ين" if hours == 2 else ""))
    elif seconds >= 60:
        minutes = seconds // 60
        return f"{minutes} دقيقة" + ("ق" if minutes >= 3 else ("تين" if minutes == 2 else "ة"))
    else:
        return f"{seconds} ثانية" + ("تين" if seconds == 2 else ("ت" if seconds >= 3 else "ة"))

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
        # أنماط الوقت المدعومة
        time_patterns = [
            r'^\d+ث$', r'^\d+ثانية$', r'^\d+ثواني$',
            r'^\d+د$', r'^\d+دقيقة$', r'^\d+دقائق$',
            r'^\d+س$', r'^\d+ساعة$', r'^\d+ساعات$',
            r'^يوم$'
        ]
        is_time = False
        for pattern in time_patterns:
            if re.match(pattern, time_part):
                is_time = True
                break
        
        if is_time:
            duration_seconds = parse_duration(time_part)
            duration_str = format_duration(duration_seconds)
            reason = parts[2] if len(parts) > 2 else "لا يوجد سبب"
        else:
            reason = time_part
            duration_str = "10 دقائق"
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

async def unmute_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر يدوي لفك الكتم عن عضو"""
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
    
    try:
        await context.bot.restrict_chat_member(
            GROUP_ID, 
            target_id, 
            permissions=telegram.ChatPermissions(can_send_messages=True)
        )
    except Exception as e:
        print(f"Unmute error: {e}")
        await update.message.reply_text(f"❌ فشل فك الكتم: {e}")
        return
    
    conn = get_db()
    conn.execute("UPDATE users SET is_muted = 0, muted_until = 0 WHERE user_id = ?", (target_id,))
    conn.commit()
    conn.close()
    
    await context.bot.send_message(
        GROUP_ID,
        f"🔓 **فك الكتم**\n\n"
        f"👤 العضو: {target_name} (@{target_username})\n"
        f"✅ تم فك الكتم ويمكنه التحدث مرة أخرى\n\n"
        f"👮 بواسطة: {admin_name}"
    )

async def unmute_user(context, user_id, send_notification=True):
    """فك الكتم عن عضو وتحديث قاعدة البيانات"""
    try:
        await context.bot.restrict_chat_member(
            GROUP_ID, 
            user_id, 
            permissions=telegram.ChatPermissions(can_send_messages=True)
        )
        print(f"✅ Unmuted user {user_id} successfully")
    except Exception as e:
        print(f"Unmute error: {e}")
    
    conn = get_db()
    conn.execute("UPDATE users SET is_muted = 0, muted_until = 0 WHERE user_id = ?", (user_id,))
    conn.commit()
    
    cursor = conn.execute("SELECT first_name, username FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    
    if send_notification and user:
        name = user["first_name"] or user["username"] or str(user_id)
        username = user["username"] or "لا يوجد"
        await context.bot.send_message(
            GROUP_ID,
            f"🔓 **انتهاء عقوبة الكتم**\n\n"
            f"👤 العضو: {name} (@{username})\n"
            f"✅ انتهت فترة العقوبة ويمكنه التحدث مرة أخرى"
        )
    
    return user if user else None

async def check_expired_mutes(app):
    """فحص الأعضاء الذين انتهت مدتهم وفك الكتم عنهم"""
    conn = get_db()
    current_time = int(time.time())
    
    cursor = conn.execute("SELECT user_id, muted_until FROM users WHERE is_muted = 1")
    all_muted = cursor.fetchall()
    conn.close()
    
    print(f"🔍 Checking {len(all_muted)} muted users...")
    
    expired_count = 0
    for user in all_muted:
        if user["muted_until"] <= current_time:
            print(f"🔓 Unmuting user {user['user_id']} (expired at {user['muted_until']}, now {current_time})")
            await unmute_user(app, user["user_id"], send_notification=True)
            expired_count += 1
    
    print(f"✅ Unmuted {expired_count} expired users")