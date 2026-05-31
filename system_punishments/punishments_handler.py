import time
from telegram import Update
from telegram.ext import ContextTypes
from shared.database import get_db
from shared.permissions import is_admin, is_super_admin
from config import GROUP_ID
from .punishments_data import MUTE_DURATIONS, DEFAULT_MUTE_DURATION

async def mute_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.message.reply_text("❌ هذا الأمر للمشرفين فقط")
        return
    
    if not update.message.reply_to_message:
        await update.message.reply_text("❌ يرجى الرد على رسالة العضو الذي تريد كتمه")
        return
    
    target_user = update.message.reply_to_message.from_user
    target_id = target_user.id
    
    # استخراج المدة والسبب
    text = update.message.text
    parts = text.split(maxsplit=2)
    
    duration_str = parts[1] if len(parts) > 1 else "5د"
    reason = parts[2] if len(parts) > 2 else "لا يوجد سبب"
    
    duration = MUTE_DURATIONS.get(duration_str, DEFAULT_MUTE_DURATION)
    until_time = int(time.time()) + duration
    
    conn = get_db()
    conn.execute("UPDATE users SET is_muted = 1, muted_until = ? WHERE user_id = ?", (until_time, target_id))
    conn.commit()
    conn.close()
    
    # كتم العضو في تليجرام
    try:
        await context.bot.restrict_chat_member(
            GROUP_ID, target_id,
            permissions=telegram.ChatPermissions(can_send_messages=False)
        )
    except:
        pass
    
    await context.bot.send_message(
        GROUP_ID,
        f"🔇 **كتم**\n\n"
        f"👤 العضو: {target_user.first_name}\n"
        f"⏱️ المدة: {duration_str}\n"
        f"📝 السبب: {reason}\n\n"
        f"👮 بواسطة: {update.effective_user.first_name}",
        parse_mode="Markdown"
    )

async def ban_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if not is_super_admin(user_id):
        await update.message.reply_text("❌ هذا الأمر للمشرف الإداري فقط")
        return
    
    if not update.message.reply_to_message:
        await update.message.reply_text("❌ يرجى الرد على رسالة العضو الذي تريد حظره")
        return
    
    target_user = update.message.reply_to_message.from_user
    target_id = target_user.id
    
    text = update.message.text
    parts = text.split(maxsplit=1)
    reason = parts[1] if len(parts) > 1 else "لا يوجد سبب"
    
    await ban_user(context, target_id, reason)
    
    await context.bot.send_message(
        GROUP_ID,
        f"🚫 **حظر**\n\n"
        f"👤 العضو: {target_user.first_name}\n"
        f"📝 السبب: {reason}\n\n"
        f"👮 بواسطة: {update.effective_user.first_name}",
        parse_mode="Markdown"
    )

async def kick_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if not is_super_admin(user_id):
        await update.message.reply_text("❌ هذا الأمر للمشرف الإداري فقط")
        return
    
    if not update.message.reply_to_message:
        await update.message.reply_text("❌ يرجى الرد على رسالة العضو الذي تريد طرده")
        return
    
    target_user = update.message.reply_to_message.from_user
    target_id = target_user.id
    
    text = update.message.text
    parts = text.split(maxsplit=1)
    reason = parts[1] if len(parts) > 1 else "لا يوجد سبب"
    
    try:
        await context.bot.ban_chat_member(GROUP_ID, target_id)
        await context.bot.unban_chat_member(GROUP_ID, target_id)
    except:
        pass
    
    await context.bot.send_message(
        GROUP_ID,
        f"👢 **طرد**\n\n"
        f"👤 العضو: {target_user.first_name}\n"
        f"📝 السبب: {reason}\n\n"
        f"👮 بواسطة: {update.effective_user.first_name}",
        parse_mode="Markdown"
    )

async def ban_user(context, user_id, reason):
    try:
        await context.bot.ban_chat_member(GROUP_ID, user_id)
    except:
        pass
    
    conn = get_db()
    conn.execute("UPDATE users SET is_banned = 1 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

async def unmute_user(context, user_id):
    try:
        await context.bot.restrict_chat_member(
            GROUP_ID, user_id,
            permissions=telegram.ChatPermissions(
                can_send_messages=True,
                can_send_media_messages=True,
                can_send_other_messages=True
            )
        )
    except:
        pass
    
    conn = get_db()
    conn.execute("UPDATE users SET is_muted = 0, muted_until = 0 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()