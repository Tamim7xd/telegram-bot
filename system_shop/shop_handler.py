import time
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
from shared.database import get_db

TITLES = {
    1: {"name": "عضو جديد 🌱", "price": 1000},
    2: {"name": "مقاتل ⚔️", "price": 2500},
    3: {"name": "ملك 👑", "price": 5000},
    4: {"name": "VIP 💎", "price": 10000},
    5: {"name": "أسطوري 🔥", "price": 20000},
}

async def shop_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton(f"{t['name']} - {t['price']} 🪙", callback_data=f"shop_{tid}")] for tid, t in TITLES.items()]
    keyboard.append([InlineKeyboardButton("🔙 إغلاق", callback_data="shop_close")])
    
    await update.message.reply_text("🛒 **السوق - اختر لقبك:**", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def shop_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    data = query.data
    
    if data == "shop_close":
        await query.edit_message_text("🔚 تم إغلاق السوق")
        return
    
    if data.startswith("shop_"):
        title_id = int(data.split("_")[1])
        title = TITLES[title_id]
        
        conn = get_db()
        
        cursor = conn.execute("SELECT title FROM user_titles WHERE user_id = ? AND title = ?", (user_id, title['name']))
        if cursor.fetchone():
            await query.edit_message_text(f"🎁 **لديك هذا اللقب بالفعل!**\n\n{title['name']}\n💰 متوفر مجاناً")
            conn.close()
            return
        
        cursor = conn.execute("SELECT balance, first_name FROM users WHERE user_id = ?", (user_id,))
        user = cursor.fetchone()
        
        if not user:
            await query.edit_message_text("❌ يرجى كتابة #ملف أولاً")
            conn.close()
            return
        
        balance = user['balance']
        
        if balance >= title['price']:
            new_balance = balance - title['price']
            conn.execute("UPDATE users SET balance = ?, title = ? WHERE user_id = ?", (new_balance, title['name'], user_id))
            conn.execute("INSERT INTO user_titles (user_id, title, purchased_at) VALUES (?, ?, ?)", (user_id, title['name'], int(time.time())))
            conn.commit()
            
            # تغيير اسم العضو في المجموعة
            try:
                from config import GROUP_ID
                new_name = f"{title['name']} {user['first_name']}"
                await context.bot.set_chat_member_title(GROUP_ID, user_id, new_name)
            except:
                pass
            
            await query.edit_message_text(f"🎉 **تهانينا!**\n\n✅ تم شراء: {title['name']}\n💰 -{title['price']} عملة\n💵 رصيدك: {new_balance} عملة")
        else:
            await query.edit_message_text(f"❌ **رصيدك غير كافٍ!**\n\n🏷️ السعر: {title['price']}\n💵 رصيدك: {balance}\n📉 تحتاج: {title['price'] - balance} عملة")
        
        conn.close()