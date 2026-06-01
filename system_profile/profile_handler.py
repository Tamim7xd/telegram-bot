import time
from telegram import Update
from telegram.ext import ContextTypes
from shared.database import get_db
from config import MESSAGE_TO_LEVEL, LEVEL_REWARD, MAX_WARNINGS

async def profile_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username or "لا يوجد"
    first_name = update.effective_user.first_name or "مستخدم"
    
    if update.message.reply_to_message:
        target = update.message.reply_to_message.from_user
        target_id = target.id
        target_name = target.first_name or "مستخدم"
        target_username = target.username or "لا يوجد"
    else:
        target_id = user_id
        target_name = first_name
        target_username = username
    
    conn = get_db()
    conn.execute("INSERT OR IGNORE INTO users (user_id, username, first_name) VALUES (?, ?, ?)", 
                 (target_id, target_username, target_name))
    conn.commit()
    
    cursor = conn.execute("SELECT balance, warnings, messages, level, title FROM users WHERE user_id = ?", (target_id,))
    user = cursor.fetchone()
    
    if not user:
        balance, warnings, messages, level, title = 1000, 0, 0, 1, None
    else:
        balance, warnings, messages, level, title = user
    
    new_level = (messages // MESSAGE_TO_LEVEL) + 1
    if new_level > level and target_id == user_id:
        reward = (new_level - level) * LEVEL_REWARD
        conn.execute("UPDATE users SET level = ?, balance = balance + ? WHERE user_id = ?", 
                     (new_level, reward, target_id))
        balance += reward
        level = new_level
        conn.commit()
    
    current = messages % MESSAGE_TO_LEVEL
    progress = "█" * (current // 10) + "░" * (10 - (current // 10))
    title_text = f"🏆 {title}" if title else ""
    
    text = f"""👤 **{target_name}** (@{target_username})

💰 الرصيد: {balance} 🪙
⚠️ التحذيرات: {warnings}/{MAX_WARNINGS}
📨 الرسائل: {messages}
🎖️ المستوى: {level}

{progress} {current}/{MESSAGE_TO_LEVEL}

{title_text}"""
    
    conn.close()
    await update.message.reply_text(text, parse_mode="Markdown")