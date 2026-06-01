from telegram import Update
from telegram.ext import ContextTypes
from shared.database import get_db
from shared.message_builder import send_and_delete
from config import MESSAGE_TO_LEVEL, LEVEL_REWARD, MAX_WARNINGS

async def profile_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username or "لا يوجد"
    first_name = update.effective_user.first_name or "مستخدم"
    
    conn = get_db()
    
    # إضافة المستخدم إذا لم يكن موجوداً
    conn.execute("INSERT OR IGNORE INTO users (user_id, username, first_name) VALUES (?, ?, ?)", 
                 (user_id, username, first_name))
    conn.commit()
    
    # جلب البيانات
    cursor = conn.execute("SELECT balance, warnings, messages, level, title FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    
    if not user:
        balance, warnings, messages, level, title = 1000, 0, 0, 1, None
    else:
        balance, warnings, messages, level, title = user
    
    # حساب المستوى الجديد
    new_level = (messages // MESSAGE_TO_LEVEL) + 1
    if new_level > level:
        reward = (new_level - level) * LEVEL_REWARD
        conn.execute("UPDATE users SET level = ?, balance = balance + ? WHERE user_id = ?", 
                     (new_level, reward, user_id))
        balance += reward
        level = new_level
        conn.commit()
        await send_and_delete(context, update.effective_chat.id, f"🎉 مبروك! وصلت للمستوى {level}\n💰 +{reward} عملة", timeout=5)
    
    # شريط التقدم
    current = messages % MESSAGE_TO_LEVEL
    total = MESSAGE_TO_LEVEL
    percent = int((current / total) * 10)
    progress = "█" * percent + "░" * (10 - percent)
    
    title_text = f"🏆 {title}" if title else ""
    
    text = f"""👤 **{first_name}** (@{username})

💰 الرصيد: {balance} 🪙
⚠️ التحذيرات: {warnings}/{MAX_WARNINGS}
📨 الرسائل: {messages}
🎖️ المستوى: {level}

{progress} {current}/{total}

{title_text}"""
    
    conn.close()
    
    await send_and_delete(context, update.effective_chat.id, text, timeout=5, reply_markup=None)