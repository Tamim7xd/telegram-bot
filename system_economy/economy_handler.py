import time
from telegram import Update
from telegram.ext import ContextTypes
from shared.database import get_db
from shared.permissions import is_admin
from shared.logger import log_action
from config import GROUP_ID, DAILY_REWARD

async def add_balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إضافة رصيد لعضو (مكافأة)"""
    user_id = update.effective_user.id
    admin_name = update.effective_user.first_name
    
    print(f"add_balance_command called by {admin_name}")  # للتصحيح
    
    if not is_admin(user_id):
        await update.message.reply_text("❌ هذا الأمر للمشرفين فقط")
        return
    
    if not update.message.reply_to_message:
        await update.message.reply_text("❌ يرجى الرد على رسالة العضو المستهدف")
        return
    
    target = update.message.reply_to_message.from_user
    target_id = target.id
    target_name = target.first_name
    
    # محاولة قراءة المبلغ من context أولاً (إذا جاء من الأمر العربي)
    amount = context.user_data.get('temp_amount')
    reason = context.user_data.get('temp_reason', "لا يوجد سبب")
    
    print(f"Amount from context: {amount}, Reason: {reason}")  # للتصحيح
    
    if amount is None:
        # قراءة من النص المباشر (إذا جاء من الأمر الإنجليزي /reward)
        text = update.message.text
        parts = text.split(maxsplit=2)
        if len(parts) < 2:
            await update.message.reply_text("❌ يرجى تحديد المبلغ\nمثال: #مكافأة 500 سبب")
            return
        try:
            amount = int(parts[1])
        except ValueError:
            await update.message.reply_text("❌ المبلغ يجب أن يكون رقماً")
            return
        reason = parts[2] if len(parts) > 2 else "لا يوجد سبب"
    
    if amount is None or amount <= 0:
        await update.message.reply_text("❌ المبلغ يجب أن يكون رقماً موجباً")
        return
    
    # تنظيف context
    context.user_data.pop('temp_amount', None)
    context.user_data.pop('temp_reason', None)
    
    # تحديث الرصيد
    conn = get_db()
    conn.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (target_id,))
    conn.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, target_id))
    
    cursor = conn.execute("SELECT balance FROM users WHERE user_id = ?", (target_id,))
    result = cursor.fetchone()
    new_balance = result["balance"] if result else amount
    
    # تسجيل العملية
    log_action(conn, user_id, admin_name, "مكافأة", target_id, target_name, reason)
    conn.commit()
    conn.close()
    
    # إرسال إشعار
    await context.bot.send_message(
        GROUP_ID,
        f"🎁 **مكافأة**\n\n"
        f"👤 العضو: {target_name}\n"
        f"💰 +{amount} عملة\n"
        f"📝 السبب: {reason}\n"
        f"💵 الرصيد الجديد: {new_balance} عملة\n\n"
        f"👮 بواسطة: {admin_name}"
    )

async def remove_balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """خصم رصيد من عضو"""
    user_id = update.effective_user.id
    admin_name = update.effective_user.first_name
    
    print(f"remove_balance_command called by {admin_name}")  # للتصحيح
    
    if not is_admin(user_id):
        await update.message.reply_text("❌ هذا الأمر للمشرفين فقط")
        return
    
    if not update.message.reply_to_message:
        await update.message.reply_text("❌ يرجى الرد على رسالة العضو المستهدف")
        return
    
    target = update.message.reply_to_message.from_user
    target_id = target.id
    target_name = target.first_name
    
    # محاولة قراءة المبلغ من context أولاً (إذا جاء من الأمر العربي)
    amount = context.user_data.get('temp_amount')
    reason = context.user_data.get('temp_reason', "لا يوجد سبب")
    
    print(f"Amount from context: {amount}, Reason: {reason}")  # للتصحيح
    
    if amount is None:
        # قراءة من النص المباشر (إذا جاء من الأمر الإنجليزي /deduct)
        text = update.message.text
        parts = text.split(maxsplit=2)
        if len(parts) < 2:
            await update.message.reply_text("❌ يرجى تحديد المبلغ\nمثال: #خصم 500 سبب")
            return
        try:
            amount = int(parts[1])
        except ValueError:
            await update.message.reply_text("❌ المبلغ يجب أن يكون رقماً")
            return
        reason = parts[2] if len(parts) > 2 else "لا يوجد سبب"
    
    if amount is None or amount <= 0:
        await update.message.reply_text("❌ المبلغ يجب أن يكون رقماً موجباً")
        return
    
    # تنظيف context
    context.user_data.pop('temp_amount', None)
    context.user_data.pop('temp_reason', None)
    
    # تحديث الرصيد
    conn = get_db()
    conn.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (target_id,))
    conn.execute("UPDATE users SET balance = balance - ? WHERE user_id = ?", (amount, target_id))
    
    cursor = conn.execute("SELECT balance FROM users WHERE user_id = ?", (target_id,))
    result = cursor.fetchone()
    new_balance = result["balance"] if result else 0
    
    # تسجيل العملية
    log_action(conn, user_id, admin_name, "خصم", target_id, target_name, reason)
    conn.commit()
    conn.close()
    
    # إرسال إشعار
    await context.bot.send_message(
        GROUP_ID,
        f"💰 **خصم**\n\n"
        f"👤 العضو: {target_name}\n"
        f"💰 -{amount} عملة\n"
        f"📝 السبب: {reason}\n"
        f"💵 الرصيد الجديد: {new_balance} عملة\n\n"
        f"👮 بواسطة: {admin_name}"
    )

async def daily_reward_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """المكافأة اليومية للعضو"""
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
    
    cursor = conn.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
    new_balance = cursor.fetchone()["balance"] if cursor.fetchone() else DAILY_REWARD
    conn.commit()
    conn.close()
    
    await update.message.reply_text(
        f"🎁 **المكافأة اليومية**\n\n"
        f"💰 +{DAILY_REWARD} عملة\n"
        f"💵 رصيدك الجديد: {new_balance} عملة\n"
        f"📅 عودة غداً لمكافأة جديدة"
    )