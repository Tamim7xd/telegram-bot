import time
import telegram
from telegram import Update
from telegram.ext import ContextTypes
from shared.database import get_db
from shared.permissions import is_admin, is_super_admin
from shared.logger import log_action
from config import GROUP_ID

MUTE_DURATIONS = {"1د": 60, "5د": 300, "10د": 600, "30د": 1800, "1س": 3600, "يوم": 86400}

async def mute_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    
    text = update.message.text.split()
    duration_str = text[1] if len(text) > 1 else "5د"
    reason = " ".join(text[2:]) if len(text) > 2 else "لا يوجد سبب"
    
    duration = MUTE_DURATIONS.get(duration_str, 300)
    until = int(time.time()) + duration
    
    try:
        await context.bot.restrict_chat_member(GROUP_ID, target_id, permissions=telegram.ChatPermissions(can_send_messages=False))
    except:
        pass
    
    conn = get_db()
    conn.execute("UPDATE users SET is_muted = 1, muted_until = ? WHERE user_id = ?", (until, target_id))
    log_action(conn, user_id, admin_name, "كتم", target_id, target_name, reason)
    conn.commit()
    conn.close()
    
    await context.bot.send_message(GROUP_ID, f"🔇 **كتم**\n\n👤 {target_name}\n⏱️ {duration_str}\n📝 {reason}\n\n👮 بواسطة: {admin_name}", parse_mode="Markdown")

async def ban_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    admin_name = update.effective_user.first_name
    
    if not is_super_admin(user_id):
        await update.message.reply_text("❌ هذا الأمر للمشرف الإداري فقط")
        return
    if not update.message.reply_to_message:
        await update.message.reply_text("❌ يرجى الرد على رسالة العضو")
        return
    
    target = update.message.reply_to_message.from_user
    target_id = target.id
    target_name = target.first_name
    
    text = update.message.text.split(maxsplit=1)
    reason = text[1] if len(text) > 1 else "لا يوجد سبب"
    
    try:
        await context.bot.ban_chat_member(GROUP_ID, target_id)
    except:
        pass
    
    conn = get_db()
    conn.execute("UPDATE users SET is_banned = 1 WHERE user_id = ?", (target_id,))
    log_action(conn, user_id, admin_name, "حظر", target_id, target_name, reason)
    conn.commit()
    conn.close()
    
    await context.bot.send_message(GROUP_ID, f"🚫 **حظر**\n\n👤 {target_name}\n📝 {reason}\n\n👮 بواسطة: {admin_name}", parse_mode="Markdown")

async def kick_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    admin_name = update.effective_user.first_name
    
    if not is_super_admin(user_id):
        await update.message.reply_text("❌ هذا الأمر للمشرف الإداري فقط")
        return
    if not update.message.reply_to_message:
        await update.message.reply_text("❌ يرجى الرد على رسالة العضو")
        return
    
    target = update.message.reply_to_message.from_user
    target_id = target.id
    target_name = target.first_name
    
    text = update.message.text.split(maxsplit=1)
    reason = text[1] if len(text) > 1 else "لا يوجد سبب"
    
    try:
        await context.bot.ban_chat_member(GROUP_ID, target_id)
        await context.bot.unban_chat_member(GROUP_ID, target_id)
    except:
        pass
    
    conn = get_db()
    log_action(conn, user_id, admin_name, "طرد", target_id, target_name, reason)
    conn.commit()
    conn.close()
    
    await context.bot.send_message(GROUP_ID, f"👢 **طرد**\n\n👤 {target_name}\n📝 {reason}\n\n👮 بواسطة: {admin_name}", parse_mode="Markdown")

async def unmute_user(context, user_id):
    try:
        await context.bot.restrict_chat_member(GROUP_ID, user_id, permissions=telegram.ChatPermissions(can_send_messages=True, can_send_media_messages=True, can_send_other_messages=True))
    except:
        pass
    
    conn = get_db()
    conn.execute("UPDATE users SET is_muted = 0, muted_until = 0 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()