from telegram import Update
from telegram.ext import ContextTypes
from shared.database import get_db

async def profile_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username or "لا يوجد"
    first_name = update.effective_user.first_name or ""
    
    conn = get_db()
    
    # إضافة المستخدم إذا لم يكن موجوداً
    conn.execute("INSERT OR IGNORE INTO users (user_id, username, first_name) VALUES (?, ?, ?)", 
                 (user_id, username, first_name))
    
    cursor = conn.execute("SELECT balance, warnings, messages, level, title FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    
    if not user:
        balance, warnings, messages, level, title = 1000, 0, 0, 1, None
    else:
        balance, warnings, messages, level, title = user
    
    # حساب المستوى الجديد بناءً على الرسائل
    new_level = (messages // 100) + 1
    if new_level > level:
        conn.execute("UPDATE users SET level = ? WHERE user_id = ?", (new_level, user_id))
        reward = (new_level - level) * 1000
        conn.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (reward, user_id))
        balance += reward
        level = new_level
        
        import asyncio
        from shared.message_builder import send_temp_message
        await send_temp_message(context, update.effective_chat.id, f"🎉 مبروك! وصلت للمستوى {level}\n💰 +{reward} عملة")
    
    # حساب شريط التقدم
    current_msgs = messages % 100
    next_level_msgs = 100
    progress_bar = "█" * (current_msgs // 10) + "░" * (10 - (current_msgs // 10))
    
    title_text = f"🏆 {title}" if title else ""
    
    text = f"""👤 **{first_name}** (@{username})

💰 الرصيد: {balance} 🪙
⚠️ التحذيرات: {warnings} / {5}
📨 الرسائل: {messages}
🎖️ المستوى: {level}

{progress_bar} {current_msgs}/{next_level_msgs}

{title_text}"""
    
    conn.commit()
    conn.close()
    
    await update.message.reply_text(text, parse_mode="Markdown")