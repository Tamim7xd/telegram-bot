import random
import asyncio
from aiogram import Dispatcher
from aiogram.types import Message
from _core.game_engine import get_random_game, save_game_session, check_answer, get_game_session, update_game_session_status
from _core.users import update_user_money
from _core.xp import add_xp
from _core.notify import bot
from config import GAME_TIME_LIMIT, DEFAULT_GAME_PRIZE_MIN, DEFAULT_GAME_PRIZE_MAX

async def cmd_game(message: Message):
    chat_id = message.chat.id
    prize = random.randint(DEFAULT_GAME_PRIZE_MIN, DEFAULT_GAME_PRIZE_MAX)
    game = await get_random_game(prize)
    if not game:
        await message.reply("⚠️ لا توجد ألعاب متاحة حالياً. راجع مجلد data/")
        return
    sent = await message.reply(game['display_text'], parse_mode="Markdown")
    await save_game_session(chat_id, sent.message_id, game['type'], game['question'], game['answer'], prize)
    asyncio.create_task(end_game_timeout(chat_id, sent.message_id, game['answer']))

async def end_game_timeout(chat_id, message_id, correct_answer):
    await asyncio.sleep(GAME_TIME_LIMIT)
    session = await get_game_session(chat_id, message_id)
    if session and session['status'] == 'waiting':
        await update_game_session_status(chat_id, message_id, 'finished')
        await bot.send_message(chat_id, f"⏰ انتهت المهلة! الإجابة الصحيحة: {correct_answer}")

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
        await message.reply(f"🎉 إجابة صحيحة! ربحت {prize} دينار و 25 XP!")
    elif prize == 0:
        await message.reply("❌ إجابة خاطئة!")

def register_games_handlers(dp: Dispatcher):
    dp.message.register(cmd_game, lambda msg: msg.text in ["#لعبة", "#العب", "#العاب"])
    dp.message.register(handle_game_answer)
