import random
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from db import execute, fetchone

games = {
    "math": [
        {"q": "5 + 3 = ?", "a": "8"},
        {"q": "10 - 4 = ?", "a": "6"}
    ],
    "riddles": [
        {"q": "شيء يمشي بلا أرجل؟", "a": "الوقت"}
    ]
}


# 🎮 عرض قائمة الألعاب
async def start_game_menu(message):

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🧠 رياضيات", callback_data="game_math")],
        [InlineKeyboardButton(text="🧩 ألغاز", callback_data="game_riddles")]
    ])

    await message.reply("🎮 اختر لعبة:", reply_markup=kb)


# 🎯 بدء لعبة
async def start_game(chat_id, game_type, bot):

    game = random.choice(games[game_type])

    msg = await bot.send_message(chat_id, game["q"])

    execute(
        "INSERT INTO game_sessions (chat_id, message_id, answer, prize) VALUES (?, ?, ?, ?)",
        (chat_id, msg.message_id, game["a"], 100)
    )


# 🎯 التحقق من الإجابة
async def process_game_answer(message):

    if not message.reply_to_message:
        return

    session = fetchone(
        "SELECT * FROM game_sessions WHERE chat_id=? AND message_id=?",
        (message.chat.id, message.reply_to_message.message_id)
    )

    if not session:
        return

    correct = session[2]

    if message.text.strip() == correct:
        await message.reply("🎉 إجابة صحيحة +100")
    else:
        await message.reply("❌ خطأ")
