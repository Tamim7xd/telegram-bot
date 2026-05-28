from telegram import InlineKeyboardMarkup, InlineKeyboardButton

def admin_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("👥 الأعضاء", callback_data="users:0")],
        [InlineKeyboardButton("❌ إغلاق", callback_data="close")]
    ])


def user_panel(uid):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ إضافة", callback_data=f"add:{uid}")],
        [InlineKeyboardButton("➖ خصم", callback_data=f"rem:{uid}")],
        [InlineKeyboardButton("🏆 لقب", callback_data=f"title:{uid}")],
        [InlineKeyboardButton("🔇 كتم", callback_data=f"mute:{uid}")],
        [InlineKeyboardButton("🚫 حظر", callback_data=f"ban:{uid}")],
        [InlineKeyboardButton("🔓 فك", callback_data=f"unban:{uid}")]
    ])
