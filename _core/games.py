import random
import asyncio
from aiogram import Dispatcher, types
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from _core.game_engine import get_random_game, save_game_session, check_answer, get_game_session, update_game_session_status
from _core.users import update_user_money
from _core.xp import add_xp
from _core.notify import bot
from config import GAME_TIME_LIMIT, DEFAULT_GAME_PRIZE_MIN, DEFAULT_GAME_PRIZE_MAX

# لوحة اختيار نوع اللعبة
async def show_game_menu(message: Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🧠 لغز", callback_data="game_puzzles"),
         InlineKeyboardButton(text="❓ سؤال عام", callback_data="game_general")],
        [InlineKeyboardButton(text="🔘 اختيار من متعدد", callback_data="game_mcq"),
         InlineKeyboardButton(text="⚡ سرعة", callback_data="game_speed")],
        [InlineKeyboardButton(text="🎲 حظ (صندوق)", callback_data="game_luck"),
         InlineKeyboardButton(text="📜 مثل شعبي", callback_data="game_proverb")],
        [InlineKeyboardButton(text="🎲 عشوائي", callback_data="game_random")]
    ])
    await message.reply("🎮 *اختر نوع اللعبة التي تريدها:*", reply_markup=keyboard, parse_mode="Markdown")

async def start_game(chat_id, message_id, game_type, prize):
    game = await get_random_game(prize, game_type)
    if not game:
        await bot.send_message(chat_id, "⚠️ هذا النوع من الألعاب لا يحتوي على أسئلة حالياً. جرب نوعاً آخر.")
        return False
    sent = await bot.send_message(chat_id, game['display_text'], parse_mode="Markdown")
    await save_game_session(chat_id, sent.message_id, game['type'], game['question'], game['answer'], prize)
    asyncio.create_task(end_game_timeout(chat_id, sent.message_id, game['answer']))
    return True

async def end_game_timeout(chat_id, message_id, correct_answer):
    await asyncio.sleep(GAME_TIME_LIMIT)
    session = await get_game_session(chat_id, message_id)
    if session and session['status'] == 'waiting':
        await update_game_session_status(chat_id, message_id, 'finished')
        await bot.send_message(chat_id, f"⏰ *انتهت المهلة!* ⏰\nالإجابة الصحيحة: `{correct_answer}`", parse_mode="Markdown")

async def handle_game_answer(message: Message):
    if not message.reply_to_message:
        return
    chat_id = message.chat.id
    msg_id = message.reply_to_message.message_id
    prize = await check_answer(chat_id, msg_id, message.text)
    if prize is None:
        return
    if prize > 0:
        await update_user_money(message.from_user.id, prize, "فوز بلعبة", None)
        await add_xp(message.from_user.id, 25, chat_id, message.from_user.full_name)
        await message.reply(f"🎉 *إجابة صحيحة!* 🎉\n💰 ربحت {prize} دينار\n⭐ +25 XP")
    elif prize == 0:
        await message.reply("❌ *إجابة خاطئة!* ❌\nحظاً أفضل في المرة القادمة.", parse_mode="Markdown")

async def handle_game_callback(callback: CallbackQuery):
    chat_id = callback.message.chat.id
    data = callback.data
    await callback.answer()
    if data.startswith("game_"):
        game_type = data.replace("game_", "")
        if game_type == "random":
            game_type = None
        prize = random.randint(DEFAULT_GAME_PRIZE_MIN, DEFAULT_GAME_PRIZE_MAX)
        success = await start_game(chat_id, callback.message.message_id, game_type, prize)
        if success:
            await callback.message.delete()
        else:
            await callback.message.edit_text("⚠️ هذا النوع من الألعاب لا يحتوي على أسئلة حالياً. جرب نوعاً آخر.")

async def cmd_game(message: Message):
    await show_game_menu(message)

def register_games_handlers(dp: Dispatcher):
    dp.message.register(cmd_game, lambda msg: msg.text in ["#لعبة", "#العب", "#العاب"])
    dp.message.register(handle_game_answer)
    dp.callback_query.register(handle_game_callback, lambda c: c.data and c.data.startswith("game_"))
