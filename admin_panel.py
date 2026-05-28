from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def admin_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("👥 الأعضاء", callback_data="users:0")],
        [InlineKeyboardButton("📊 الإحصائيات", callback_data="stats")],
        [InlineKeyboardButton("📢 إرسال رسالة", callback_data="broadcast")],
        [InlineKeyboardButton("🚫 المخالفات", callback_data="punish")],
        [InlineKeyboardButton("❌ إغلاق", callback_data="close")]
    ])
