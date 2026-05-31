import random, asyncio
from aiogram import Dispatcher
from aiogram.types import Message
from _core.game_engine import get_random_game, save_game_session, check_answer
from _core.users import update_user_money
from _core.xp import add_xp
from _core.notify import bot, send_auto_delete
from config import GAME_TIME_LIMIT, DEFAULT_GAME_PRIZE_MIN, DEFAULT_GAME_PRIZE_MAX, CURRENCY_NAME

# قاموس لتتبع حالة المستخدمين (انتظار اختيار لعبة، انتظار إجابة)
user_game_context = {}

def set_user_game_context(user_id: int, state: str):
    user_game_context[user_id] = state

def clear_user_game_context(user_id: int):
    user_game_context.pop(user_id, None)

def is_user_in_game(user_id: int, state: str = None):
    if state:
        return user_game_context.get(user_id) == state
    return user_id in user_game_context

# قاموس لتخزين بيانات اللعبة النشطة لكل مستخدم
active_games = {}  # {user_id: {"message_id": int, "chat_id": int, "correct_answer": str, "prize": int}}

async def handle_game_command(message: Message, game_name: str):
    """يُستدعى عندما يكتب المستخدم أمر لعبة مثل /لغز"""
    user_id = message.from_user.id
    chat_id = message.chat.id
    if not is_user_in_game(user_id, "waiting_choice"):
        # إذا لم يكن في حالة انتظار، ربما يحاول الغش، نحذف الأمر
        await message.delete()
        return
    # إزالة حالة الانتظار
    clear_user_game_context(user_id)
    # بدء اللعبة
    game_map = {
        "لغز": "puzzles",
        "سؤال_عام": "general_qa",
        "اختيار_من_متعدد": "mcq",
        "سرعة": "speed_words",
        "مثل_شعبي": "proverbs",
        "حظ": "luck_boxes"
    }
    game_type = game_map.get(game_name)
    if not game_type:
        await send_auto_delete(chat_id, "⚠️ نوع لعبة غير معروف", delay=10)
        await message.delete()
        return
    await start_game(message, game_type)
    # حذف أمر اللعبة بعد التنفيذ
    await message.delete()

async def start_game(message: Message, game_type: str):
    chat_id = message.chat.id
    user_id = message.from_user.id
    prize = random.randint(DEFAULT_GAME_PRIZE_MIN, DEFAULT_GAME_PRIZE_MAX)
    game = await get_random_game(prize, game_type)
    if not game:
        await send_auto_delete(chat_id, "⚠️ لا توجد أسئلة لهذا النوع حالياً.", delay=10)
        return
    # إرسال السؤال
    sent = await bot.send_message(chat_id, game['display_text'])
    # تخزين جلسة اللعبة النشطة
    active_games[user_id] = {
        "message_id": sent.message_id,
        "chat_id": chat_id,
        "correct_answer": game['answer'],
        "prize": game['prize'],
        "game_type": game_type
    }
    # وضع المستخدم في حالة انتظار إجابة
    set_user_game_context(user_id, "answering")
    # حفظ الجلسة في قاعدة البيانات للاستخدام الاختياري
    await save_game_session(chat_id, sent.message_id, game['type'], game['question'], game['answer'], prize, user_id)
    # جدولة حذف السؤال بعد 10 ثوانٍ إذا لم تتم الإجابة
    asyncio.create_task(delete_question_after_timeout(user_id, sent.message_id, chat_id, game['answer']))

async def delete_question_after_timeout(user_id, msg_id, chat_id, correct_answer):
    await asyncio.sleep(GAME_TIME_LIMIT)
    if user_id in active_games and active_games[user_id].get("message_id") == msg_id:
        # إزالة الجلسة
        active_games.pop(user_id, None)
        clear_user_game_context(user_id)
        await send_auto_delete(chat_id, f"⏰ انتهت المهلة! الإجابة الصحيحة: {correct_answer}", delay=10)
        # حذف رسالة السؤال بعد انتهاء المهلة
        try:
            await bot.delete_message(chat_id, msg_id)
        except:
            pass

async def handle_game_answer(message: Message):
    user_id = message.from_user.id
    if user_id not in active_games:
        # ليس لديه لعبة نشطة، نتجاهل
        return
    game = active_games[user_id]
    user_answer = message.text.strip().lower()
    correct = game['correct_answer'].strip().lower()
    chat_id = game['chat_id']
    question_msg_id = game['message_id']

    # مقارنة الإجابة (بدون حساسية حالة الأحرف)
    if user_answer == correct:
        # إجابة صحيحة
        await update_user_money(user_id, game['prize'], "فوز بلعبة", None)
        await add_xp(user_id, 25, chat_id, message.from_user.full_name)
        result_text = f"🎉 <b>إجابة صحيحة!</b>\n💰 +{game['prize']} {CURRENCY_NAME}\n⭐ +25 XP"
        await send_auto_delete(chat_id, result_text, delay=10, parse_mode="HTML")
    else:
        result_text = f"❌ <b>إجابة خاطئة!</b>\nالإجابة الصحيحة هي: {correct}"
        await send_auto_delete(chat_id, result_text, delay=10, parse_mode="HTML")

    # حذف رسالة السؤال والإجابة (رسالة المستخدم) والنتيجة (النتيجة تحذف بعد 10 ثوانٍ)
    try:
        await bot.delete_message(chat_id, question_msg_id)
        await message.delete()
    except:
        pass
    # إزالة الجلسة النشطة
    active_games.pop(user_id, None)
    clear_user_game_context(user_id)

def register_games_handlers(dp: Dispatcher):
    # لا نحتاج لتسجيل أي معالج هنا لأن الألعاب تُدار من events.py
    pass
