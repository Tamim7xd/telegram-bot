from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def panel():

    return InlineKeyboardMarkup(inline_keyboard=[

        [
            InlineKeyboardButton("👥 المستخدمين", callback_data="users"),
            InlineKeyboardButton("🎮 الألعاب", callback_data="games")
        ],
        [
            InlineKeyboardButton("💰 مكافآت", callback_data="reward_all")
        ]
    ])


def games_menu():

    return InlineKeyboardMarkup(inline_keyboard=[

        [InlineKeyboardButton("❓ أسئلة", callback_data="game_mcq")],
        [InlineKeyboardButton("🧩 ألغاز", callback_data="game_puzzles")],
        [InlineKeyboardButton("📖 حكم", callback_data="game_proverbs")],
        [InlineKeyboardButton("⚡ سرعة", callback_data="game_speed")],
        [InlineKeyboardButton("🎁 حظ", callback_data="game_luck")],
        [InlineKeyboardButton("🌍 عام", callback_data="game_general")]
    ])
