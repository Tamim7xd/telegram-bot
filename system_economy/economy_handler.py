from telegram import Update
from telegram.ext import ContextTypes
from shared.database import get_db
from shared.permissions import is_admin, is_super_admin
from config import GROUP_ID

async def add_balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.message.reply_text("❌ هذا الأمر للمشرفين فقط")
        return
    
    if not update.message.reply_to_message:
        await update.message.reply_text("❌ يرجى الرد على رسالة العضو الذي تريد إعطاءه مكافأة")
        return
    
    target_user = update.message.reply_to_message.from_user
    target_id = target_user.id
    
    text = update.message.text
    parts = text.split(maxsplit=2)
    
    if len(parts) < 2:
        await update.message.reply_text("❌ يرجى تحديد المبلغ\nمثال: #مكافأة 500 سبب اختياري")
        return
    
    try:
        amount = int(parts[1])
    except:
        await update.message.reply_text("❌ المبلغ يجب أن يكون رقماً")
        return
    
    reason = parts[2] if len(parts) > 2 else "لا يوجد سبب"
    
    conn = get_db()
    conn.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (target_id,))
    conn.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, target_id))
    
    cursor = conn.execute("SELECT balance FROM users WHERE user_id = ?", (target_id,))
    new_balance = cursor.fetchone()["balance"]
    
    import time
    conn.execute(
        "INSERT INTO logs (admin_id, action, target_id, reason, timestamp) VALUES (?, ?, ?, ?, ?)",
        (user_id, "مكافأة", target_id, reason, int(time.time()))
    )
    conn.commit()
    conn.close()
    
    await context.bot.send_message(
        GROUP_ID,
        f"🎁 **مكافأة**\n\n"
        f"👤 العضو: {target_user.first_name}\n"
        f"💰 المبلغ: {amount} عملة\n"
        f"📝 السبب: {reason}\n"
        f"💵 الرصيد الجديد: {new_balance} عملة\n\n"
        f"👮 بواسطة: {update.effective_user.first_name}",
        parse_mode="Markdown"
    )

async def remove_balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.message.reply_text("❌ هذا الأمر للمشرفين فقط")
        return
    
    if not update.message.reply_to_message:
        await update.message.reply_text("❌ يرجى الرد على رسالة العضو الذي تريد خصم رصيده")
        return
    
    target_user = update.message.reply_to_message.from_user
    target_id = target_user.id
    
    text = update.message.text
    parts = text.split(maxsplit=2)
    
    if len(parts) < 2:
        await update.message.reply_text("❌ يرجى تحديد المبلغ\nمثال: #خصم 500 سبب اختياري")
        return
    
    try:
        amount = int(parts[1])
    except:
        await update.message.reply_text("❌ المبلغ يجب أن يكون رقماً")
        return
    
    reason = parts[2] if len(parts) > 2 else "لا يوجد سبب"
    
    conn = get_db()
    conn.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (target_id,))
    conn.execute("UPDATE users SET balance = balance - ? WHERE user_id = ?", (amount, target_id))
    
    cursor = conn.execute("SELECT balance FROM users WHERE user_id = ?", (target_id,))
    new_balance = cursor.fetchone()["balance"]
    
    import time
    conn.execute(
        "INSERT INTO logs (admin_id, action, target_id, reason, timestamp) VALUES (?, ?, ?, ?, ?)",
        (user_id, "خصم", target_id, reason, int(time.time()))
    )
    conn.commit()
    conn.close()
    
    await context.bot.send_message(
        GROUP_ID,
        f"💰 **خصم**\n\n"
        f"👤 العضو: {target_user.first_name}\n"
        f"💰 المبلغ: {amount} عملة\n"
        f"📝 السبب: {reason}\n"
        f"💵 الرصيد الجديد: {new_balance} عملة\n\n"
        f"👮 بواسطة: {update.effective_user.first_name}",
        parse_mode="Markdown"
    )

async def daily_reward_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    import time
    
    conn = get_db()
    cursor = conn.execute("SELECT last_daily FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    
    today = time.strftime("%Y-%m-%d")
    last_daily = result["last_daily"] if result else None
    
    if last_daily == today:
        await update.message.reply_text("⏳ لقد حصلت على مكافأتك اليومية بالفعل! عودة غداً.")
        conn.close()
        return
    
    from .economy_data import DAILY_REWARD
    conn.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    conn.execute("UPDATE users SET balance = balance + ?, last_daily = ? WHERE user_id = ?", 
                 (DAILY_REWARD, today, user_id))
    conn.commit()
    conn.close()
    
    await update.message.reply_text(f"🎁 **المكافأة اليومية**\n\n💰 +{DAILY_REWARD} عملة\n📅 عودة غداً لمكافأة جديدة", parse_mode="Markdown")