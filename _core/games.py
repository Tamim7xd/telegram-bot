import random, asyncio
from aiogram import Dispatcher
from aiogram.types import Message
from _core.game_engine import get_random_game, save_game_session, check_answer
from _core.users import update_user_money
from _core.xp import add_xp
from _core.notify import bot, send_auto_delete
from config import GAME_TIME_LIMIT, DEFAULT_GAME_PRIZE_MIN, DEFAULT_GAME_PRIZE_MAX, CURRENCY_NAME

async def start_game_with_choice(message: Message, game_type: str):
    chat_id = message.chat.id
    prize = random.randint(DEFAULT_GAME_PRIZE_MIN, DEFAULT_GAME_PRIZE_MAX)
    game = await get_random_game(prize, game_type)
    if not game:
        await send_auto_delete(chat_id, "⚠️ لا توجد أسئلة لهذا النوع حالياً.")
        return
    sent = await bot.send_message(chat_id, game['display_text'])
    await save_game_session(chat_id, sent.message_id, game['type'], game['question'], game['answer'], prize)
    asyncio.create_task(end_game_timeout(chat_id, sent.message_id, game['answer']))

async def end_game_timeout(chat_id, msg_id, correct_answer):
    await asyncio.sleep(GAME_TIME_LIMIT)
    await send_auto_delete(chat_id, f"⏰ انتهت المهلة! الإجابة: {correct_answer}")

async def handle_game_answer(message: Message):
    if not message.reply_to_message:
        return
    prize = await check_answer(message.chat.id, message.reply_to_message.message_id, message.text)
    if prize is None:
        return
    if prize > 0:
        await update_user_money(message.from_user.id, prize, "فوز بلعبة", None)
        await add_xp(message.from_user.id, 25, message.chat.id, message.from_user.full_name)
        await send_auto_delete(message.chat.id, f"🎉 فوز! +{prize:,} {CURRENCY_NAME} +25 XP")
    else:
        await message.reply("❌ إجابة خاطئة")

def register_games_handlers(dp: Dispatcher):
    dp.message.register(handle_game_answer)
