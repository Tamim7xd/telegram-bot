import random
from aiogram import Dispatcher, types
from aiogram.types import Message
from core.game_engine import get_random_game, check_answer, save_game_session, get_game_session
from core.users import update_user_money, update_user_xp, get_user
from core.xp import add_xp
from core.notify import bot
from config import GAME_TIME_LIMIT, DEFAULT_GAME_PRIZE_MIN, DEFAULT_GAME_PRIZE_MAX

async def cmd_game(message: Message):
    chat_id = message.chat.id
    # التحقق من عدم وجود لعبة نشطة (يمكن تحسينه لاحقاً)
    game = await get_random_game()
    prize = random.randint(DEFAULT_GAME_PRIZE_MIN, DEFAULT_GAME_PRIZE_MAX)
    # إرسال رسالة اللعبة
    sent = await message.reply(game['display_text'])
    # حفظ الجلسة
    await save_game_session(chat_id, sent.message_id, game['type'], game['question'], game['answer'], prize)
    # جدولة انتهاء المهلة بعد GAME_TIME_LIMIT ثانية
    import asyncio
    asyncio.create_task(end_game_timeout(chat_id, sent.message_id))

async def end_game_timeout(chat_id, message_id):
    await asyncio.sleep(GAME_TIME_LIMIT)
    session = await get_game_session(chat_id, message_id)
    if session and session['status'] == 'waiting':
        await bot.send_message(chat_id, f"⏰ انتهت المهلة! الإجابة الصحيحة: {session['answer']}")

def register_games_handlers(dp: Dispatcher):
    dp.message.register(cmd_game, lambda msg: msg.text in ["#لعبة", "#العب", "#العاب"])
