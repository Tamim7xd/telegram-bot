import random, asyncio
from aiogram import Dispatcher
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from _core.game_engine import get_random_game, save_game_session, check_answer
from _core.users import update_user_money
from _core.xp import add_xp
from _core.notify import bot
from config import GAME_TIME_LIMIT, DEFAULT_GAME_PRIZE_MIN, DEFAULT_GAME_PRIZE_MAX, CURRENCY_NAME

GAME_TYPES = {
    "puzzles": "🧠 لغز",
    "general_qa": "❓ سؤال عام",
    "mcq": "🔘 اختيار من متعدد",
    "speed_words": "⚡ سرعة",
    "proverbs": "📜 مثل شعبي",
    "luck_boxes": "🎲 حظ"
}

async def show_game_menu(message: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=GAME_TYPES["puzzles"], callback_data="game_puzzles"),
         InlineKeyboardButton(text=GAME_TYPES["general_qa"], callback_data="game_general")],
        [InlineKeyboardButton(text=GAME_TYPES["mcq"], callback_data="game_mcq"),
         InlineKeyboardButton(text=GAME_TYPES["speed_words"], callback_data="game_speed_words")],
        [InlineKeyboardButton(text=GAME_TYPES["proverbs"], callback_data="game_proverbs"),
         InlineKeyboardButton(text=GAME_TYPES["luck_boxes"], callback_data="game_luck_boxes")],
        [InlineKeyboardButton(text="🎲 عشوائي", callback_data="game_random")]
    ])
    await message.reply("🎮 اختر نوع اللعبة:", reply_markup=kb)

async def start_game(chat_id, game_type, prize):
    game = await get_random_game(prize, game_type)
    if not game:
        await bot.send_message(chat_id, "⚠️ لا توجد أسئلة حالياً.")
        return False
    sent = await bot.send_message(chat_id, game['display_text'], parse_mode="Markdown")
    await save_game_session(chat_id, sent.message_id, game['type'], game['question'], game['answer'], prize)
    asyncio.create_task(end_game_timeout(chat_id, sent.message_id, game['answer']))
    return True

async def end_game_timeout(chat_id, msg_id, correct):
    await asyncio.sleep(GAME_TIME_LIMIT)
    await bot.send_message(chat_id, f"⏰ انتهت المهلة! الإجابة: {correct}")

async def handle_game_answer(message: Message):
    if not message.reply_to_message:
        return
    prize = await check_answer(message.chat.id, message.reply_to_message.message_id, message.text)
    if prize is None:
        return
    if prize > 0:
        fixed = 10
        await update_user_money(message.from_user.id, fixed, "فوز بلعبة", None)
        await add_xp(message.from_user.id, 25, message.chat.id, message.from_user.full_name)
        await bot.send_message(message.chat.id, f"🎉 فوز! +{fixed} {CURRENCY_NAME} و +25 XP")
    elif prize == 0:
        await message.reply("❌ خطأ")

async def game_callback(callback: CallbackQuery):
    await callback.answer("جاري التحضير...")
    game_type = callback.data.replace("game_", "")
    if game_type == "random":
        game_type = None
    prize = random.randint(DEFAULT_GAME_PRIZE_MIN, DEFAULT_GAME_PRIZE_MAX)
    await callback.message.delete()
    await start_game(callback.message.chat.id, game_type, prize)

async def cmd_game(message: Message):
    await show_game_menu(message)

def register_games_handlers(dp: Dispatcher):
    dp.message.register(cmd_game, lambda m: m.text in ["#لعبة", "#العب", "#العاب"])
    dp.message.register(handle_game_answer)
    dp.callback_query.register(game_callback, lambda c: c.data.startswith("game_"))
