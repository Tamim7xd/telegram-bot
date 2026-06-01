from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
from shared.database import get_db
from .shop_data import TITLES, SHOP_MENU

async def shop_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = []
    for item in SHOP_MENU:
        keyboard.append([InlineKeyboardButton(item["name"], callback_data=f"shop_{item['id']}")])
    keyboard.append([InlineKeyboardButton("🔙 إغلاق", callback_data="shop_close")])
    
    await update.message.reply_text(
        "🛒 **السوق - اختر لقبك:**\n\n"
        "اضغط على اللقب لشرائه",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def shop_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    username = query.from_user.username or "لا يوجد"
    data = query.data
    
    if data == "shop_close":
        await query.edit_message_text("🔚 تم إغلاق السوق")
        return
    
    if data.startswith("shop_"):
        title_id = int(data.split("_")[1])
        title_data = TITLES.get(title_id)
        
        if not title_data:
            await query.edit_message_text("❌ هذا اللقب غير موجود")
            return
        
        title_name = title_data["name"]
        title_price = title_data["price"]
        
        conn = get_db()
        
        # التحقق إذا كان المستخدم يملك اللقب
        cursor = conn.execute("SELECT title FROM users WHERE user_id = ?", (user_id,))
        current = cursor.fetchone()
        
        cursor = conn.execute("SELECT title FROM user_titles WHERE user_id = ? AND title = ?", (user_id, title_name))
        already_owned = cursor.fetchone()
        
        if already_owned:
            await query.edit_message_text(f"🎁 **لديك هذا اللقب بالفعل!**\n\n🏆 {title_name}\n💰 متوفر مجاناً")
            conn.close()
            return
        
        cursor = conn.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
        user = cursor.fetchone()
        
        if not user:
            conn.execute("INSERT INTO users (user_id, username) VALUES (?, ?)", (user_id, username))
            balance = 1000
        else:
            balance = user["balance"]
        
        if balance >= title_price:
            new_balance = balance - title_price
            conn.execute("UPDATE users SET balance = ?, title = ? WHERE user_id = ?", (new_balance, title_name, user_id))
            conn.execute("INSERT INTO user_titles (user_id, title, purchased_at) VALUES (?, ?, ?)", 
                         (user_id, title_name, int(__import__('time').time())))
            conn.commit()
            
            await query.edit_message_text(
                f"🎉 **تهانينا!**\n\n"
                f"✅ تم شراء اللقب: {title_name}\n"
                f"💰 تم خصم {title_price} عملة\n"
                f"💵 رصيدك: {new_balance} عملة"
            )
        else:
            await query.edit_message_text(
                f"❌ **رصيدك غير كافٍ!**\n\n"
                f"🏷️ السعر: {title_price} عملة\n"
                f"💵 رصيدك: {balance} عملة\n"
                f"📉 تحتاج: {title_price - balance} عملة"
            )
        
        conn.close()