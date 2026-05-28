from telegram import InlineKeyboardMarkup, InlineKeyboardButton

def admin_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("👥 الأعضاء", callback_data="users")],
        [InlineKeyboardButton("📊 الإحصائيات", callback_data="stats")]
    ])
