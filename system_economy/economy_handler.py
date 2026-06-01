import time
from telegram import Update
from telegram.ext import ContextTypes
from shared.database import get_db
from shared.permissions import is_admin
from shared.logger import log_action
from config import GROUP_ID, DAILY_REWARD

async def add_balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    if len(text) < 2:
        await update.message.reply_text("❌ يرجى تحديد المبلغ\nمثال: #خصم 500 سبب")
        return
    
    try:
        amount = int(text[1])
    except:
        await update.message.reply_text("❌ المبلغ يجب أن يكون رقماً")
        return
    
    reason = " ".join(text[2:]) if len(text) > 2 else "لا يوجد سبب"
    
    conn = get_db()
    conn.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (target_id,))
    conn.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, target_id))
    
    cursor = conn.execute("SELECT balance FROM users WHERE user_id = ?", (target_id,))
    new_balance = cursor.fetchone()["balance"]
    
    log_action(conn, user_id, admin_name, "مكافأة", target_id, target_name, reason)
    conn.commit()
    conn.close()
    
    await context.bot.send_message(GROUP_ID, f"🎁 مكافأة\n\n👤 {target_name}\n💰 +{amount} عملة\n📝 {reason}\n💵 الرصيد الجديد: {new_balance}\n\n👮 بواسطة: {admin_name}")

async def remove_balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    if len(text) < 2:
        await update.message.reply_text("❌ يرجى تحديد المبلغ\nمثال: #خصم 500 سبب")
        return
    
    try:
        amount = int(text[1])
    except:
        await update.message.reply_text("❌ المبلغ يجب أن يكون رقماً")
        return
    
    reason = " ".join(text[2:]) if len(text) > 2 else "لا يوجد سبب"
    
    conn = get_db()
    conn.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (target_id,))
    conn.execute("UPDATE users SET balance = balance - ? WHERE user_id = ?", (amount, target_id))
    
    cursor = conn.execute("SELECT balance FROM users WHERE user_id = ?", (target_id,))
    new_balance = cursor.fetchone()["balance"]
    
    log_action(conn, user_id, admin_name, "خصم", target_id, target_name, reason)
    conn.commit()
    conn.close()
    
    await context.bot.send_message(GROUP_ID, f"💰 خصم\n\n👤 {target_name}\n💰 -{amount} عملة\n📝 {reason}\n💵 الرصيد الجديد: {new_balance}\n\n👮 بواسطة: {admin_name}")

async def daily_reward_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    conn = get_db()
    cursor = conn.execute("SELECT last_daily FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    today = time.strftime("%Y-%m-%d")
    
    if result and result["last_daily"] == today:
        await update.message.reply_text("⏳ حصلت على مكافأتك اليومية بالفعل! عودة غداً")
        conn.close()
        return
    
    conn.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    conn.execute("UPDATE users SET balance = balance + ?, last_daily = ? WHERE user_id = ?", (DAILY_REWARD, today, user_id))
    conn.commit()
    conn.close()
    
    await update.message.reply_text(f"🎁 المكافأة اليومية\n\n💰 +{DAILY_REWARD} عملة\n📅 عودة غداً")