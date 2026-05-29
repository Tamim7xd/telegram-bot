import random, asyncio
from aiogram import Dispatcher
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from _core.game_engine import get_random_game, save_game_session, check_answer, get_game_session, update_game_session_status
from _core.users import update_user_money
from _core.xp import add_xp
from _core.notify import bot
from config import GAME_TIME_LIMIT, DEFAULT_GAME_PRIZE_MIN, DEFAULT_GAME_PRIZE_MAX, CURRENCY_NAME

async def show_game_menu(message: Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🧠 لغز", callback_data="game_puzzles"),
         InlineKeyboardButton(text="❓ سؤال عام", callback_data="game_general")],
        [InlineKeyboardButton(text="🔘 اختيار من متعدد", callback_data="game_mcq"),
         InlineKeyboardButton(text="⚡ سرعة", callback_data="game_speed")],
        [InlineKeyboardButton(text="🎲 حظ", callback_data="game_luck"),
         InlineKeyboardButton(text="📜 مثل", callback_data="game_proverb")],
        [InlineKeyboardButton(text="🎲 عشوائي", callback_data="game_random")]
    ])
    await message.reply("🎮 *اختر نوع اللعبة:*", reply_markup=keyboard, parse_mode="Markdown")

async def start_game(chat_id, game_type, prize):
    game = await get_random_game(prize, game_type)
    if not game:
        await bot.send_message(chat_id, "⚠️ هذا النوع لا يحتوي على أسئلة حالياً. جرب نوعاً آخر.")
        return False
    sent = await bot.send_message(chat_id, game['display_text'], parse_mode="Markdown")
    await save_game_session(chat_id, sent.message_id, game['type'], game['question'], game['answer'], prize)
    asyncio.create_task(end_game_timeout(chat_id, sent.message_id, game['answer']))
    return True

async def end_game_timeout(chat_id, msg_id, correct):
    await asyncio.sleep(GAME_TIME_LIMIT)
    session = await get_game_session(chat_id, msg_id)
    if session and session['status'] == 'waiting':
        await update_game_session_status(chat_id, msg_id, 'finished')
        await bot.send_message(chat_id, f"⏰ *انتهت المهلة!*\nالإجابة الصحيحة: `{correct}`", parse_mode="Markdown")

async def handle_game_answer(message: Message):
    if not message.reply_to_message:
        return
    prize = await check_answer(message.chat.id, message.reply_to_message.message_id, message.text)
    if prize is None:
        return
    if prize > 0:
        await update_user_money(message.from_user.id, prize, "فوز بلعبة", None)
        await add_xp(message.from_user.id, 25, message.chat.id, message.from_user.full_name)
        await message.reply(f"🎉 *إجابة صحيحة!*\n💰 +{prize} {CURRENCY_NAME}\n⭐ +25 XP", parse_mode="Markdown")
    elif prize == 0:
        await message.reply("❌ *إجابة خاطئة!*", parse_mode="Markdown")

async def game_callback(callback: CallbackQuery):
    await callback.answer("جاري تحضير اللعبة...")
    data = callback.data
    if not data.startswith("game_"):
        return
    game_type = data.replace("game_", "")
    if game_type == "random":
        game_type = None
    prize = random.randint(DEFAULT_GAME_PRIZE_MIN, DEFAULT_GAME_PRIZE_MAX)
    await callback.message.delete()
    await start_game(callback.message.chat.id, game_type, prize)

async def cmd_game(message: Message):
    await show_game_menu(message)

def register_games_handlers(dp: Dispatcher):
    dp.message.register(cmd_game, lambda m: m.text and m.text in ["#لعبة", "#العب", "#العاب"])
    dp.message.register(handle_game_answer)
    dp.callback_query.register(game_callback, lambda c: c.data and c.data.startswith("game_"))
