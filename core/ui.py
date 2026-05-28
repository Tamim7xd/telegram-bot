from telegram import InlineKeyboardMarkup, InlineKeyboardButton

def admin_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("👥 الأعضاء", callback_data="users:0")],
        [InlineKeyboardButton("❌ إغلاق", callback_data="close")]
    ])


def users_page(page=0):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("👤 عضو 1", callback_data="user:1")],
        [InlineKeyboardButton("👤 عضو 2", callback_data="user:2")],
        [InlineKeyboardButton("⬅️➡️", callback_data=f"users:{page}")],
        [InlineKeyboardButton("🏠 رجوع", callback_data="home")]
    ])


def user_panel(uid):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💰 إضافة", callback_data=f"add:{uid}")],
        [InlineKeyboardButton("💸 خصم", callback_data=f"rem:{uid}")],
        [InlineKeyboardButton("🏆 لقب", callback_data=f"title:{uid}")],
        [InlineKeyboardButton("🔇 كتم", callback_data=f"mute:{uid}")],
        [InlineKeyboardButton("🚫 حظر", callback_data=f"ban:{uid}")],
        [InlineKeyboardButton("🔓 فك", callback_data=f"unban:{uid}")]
    ])
