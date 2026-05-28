from telegram import InlineKeyboardButton, InlineKeyboardMarkup


# =========================
# ADMIN MENU
# =========================
def admin_menu():

    keyboard = [

        [
            InlineKeyboardButton(
                "👥 الأعضاء",
                callback_data="users"
            )
        ],

        [
            InlineKeyboardButton(
                "📊 الإحصائيات",
                callback_data="stats"
            )
        ],

        [
            InlineKeyboardButton(
                "🚫 المخالفين",
                callback_data="bad"
            )
        ],

        [
            InlineKeyboardButton(
                "❌ إغلاق",
                callback_data="close"
            )
        ]
    ]

    return InlineKeyboardMarkup(keyboard)
