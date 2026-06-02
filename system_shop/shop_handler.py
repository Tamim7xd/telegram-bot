import time
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
from shared.database import get_db

# قائمة الألقاب الافتراضية
TITLES = {
    1: {"name": "عضو جديد 🌱", "price": 1000},
    2: {"name": "مقاتل ⚔️", "price": 2500},
    3: {"name": "ملك 👑", "price": 5000},
    4: {"name": "VIP 💎", "price": 10000},
    5: {"name": "أسطوري 🔥", "price": 20000},
}

async def shop_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر #سوق - عرض أزرار الألقاب للمستخدمين"""
    keyboard = [[InlineKeyboardButton(f"{t['name']} - {t['price']} 🪙", callback_data=f"shop_buy_{tid}")] for tid, t in TITLES.items()]
    keyboard.append([InlineKeyboardButton("🔙 إغلاق", callback_data="shop_close")])
    
    await update.message.reply_text("🛒 **السوق - اختر لقبك:**", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def shop_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالج أزرار السوق"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    data = query.data
    
    if data == "shop_close":
        await query.edit_message_text("🔚 تم إغلاق السوق")
        return
    
    if data.startswith("shop_buy_"):
        # شراء لقب
        title_id = int(data.split("_")[2])
        title = TITLES[title_id]
        
        conn = get_db()
        
        # التحقق إذا كان المستخدم يملك اللقب بالفعل
        cursor = conn.execute("SELECT title FROM user_titles WHERE user_id = ? AND title = ?", (user_id, title['name']))
        if cursor.fetchone():
            await query.edit_message_text(f"🎁 **لديك هذا اللقب بالفعل!**\n\n{title['name']}\n💰 متوفر مجاناً", parse_mode="Markdown")
            conn.close()
            return
        
        # التحقق من الرصيد
        cursor = conn.execute("SELECT balance, first_name FROM users WHERE user_id = ?", (user_id,))
        user = cursor.fetchone()
        
        if not user:
            await query.edit_message_text("❌ يرجى كتابة #ملف أولاً")
            conn.close()
            return
        
        balance = user['balance']
        first_name = user['first_name']
        
        if balance >= title['price']:
            new_balance = balance - title['price']
            conn.execute("UPDATE users SET balance = ?, title = ? WHERE user_id = ?", (new_balance, title['name'], user_id))
            conn.execute("INSERT INTO user_titles (user_id, title, purchased_at) VALUES (?, ?, ?)", (user_id, title['name'], int(time.time())))
            conn.commit()
            
            # ========== تغيير اسم العضو في المجموعة ==========
            try:
                from config import GROUP_ID
                new_name = f"{title['name']} {first_name}"
                await context.bot.set_chat_member_title(GROUP_ID, user_id, new_name)
                print(f"✅ Changed name of user {user_id} to: {new_name}")
            except Exception as e:
                print(f"Error changing name: {e}")
            # ================================================
            
            await query.edit_message_text(
                f"🎉 **تهانينا!**\n\n"
                f"✅ تم شراء: {title['name']}\n"
                f"💰 -{title['price']} عملة\n"
                f"💵 رصيدك: {new_balance} عملة",
                parse_mode="Markdown"
            )
        else:
            await query.edit_message_text(
                f"❌ **رصيدك غير كافٍ!**\n\n"
                f"🏷️ السعر: {title['price']} عملة\n"
                f"💵 رصيدك: {balance} عملة\n"
                f"📉 تحتاج: {title['price'] - balance} عملة",
                parse_mode="Markdown"
            )
        
        conn.close()
