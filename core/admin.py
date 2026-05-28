from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from core.service import is_admin


def admin_menu():
    keyboard = [
        [InlineKeyboardButton("👥 المستخدمين", callback_data="admin_users")],
        [InlineKeyboardButton("🏆 الترتيب", callback_data="admin_top")],
        [InlineKeyboardButton("📊 الإحصائيات", callback_data="admin_stats")],
        [InlineKeyboardButton("📢 إرسال للجميع", callback_data="admin_broadcast")]
    ]

    return InlineKeyboardMarkup(keyboard)
