import random, asyncio
from aiogram import Dispatcher
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from _core.game_engine import get_random_game, save_game_session, check_answer
from _core.users import update_user_money
from _core.xp import add_xp
from _core.notify import bot, send_auto_delete
from config import GAME_TIME_LIMIT, DEFAULT_GAME_PRIZE_MIN, DEFAULT_GAME_PRIZE_MAX, CURRENCY_NAME

# قاموس لتخزين بيانات اللعبة النشطة لكل مستخدم (للتحقق من أن من بدأ اللعبة هو من يجيب)
active_games = {}  # {user_id: {"message_id": int, "chat_id": int, "correct_answer": str, "prize": int, "game_type": str}}

async def show_game_menu(message: Message):
    """إظهار أزرار الألعاب (تختفي بعد 3 ثوانٍ)"""
    user_id = message.from_user.id
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🧠 لغز", callback_data=f"game_puzzles_{user_id}"),
         InlineKeyboardButton(text="❓ سؤال عام", callback_data=f"game_general_{user_id}")],
        [InlineKeyboardButton(text="🔘 اختيار من متعدد", callback_data=f"game_mcq_{user_id}"),
         InlineKeyboardButton(text="⚡ سرعة", callback_data=f"game_speed_{user_id}")],
        [InlineKeyboardButton(text="📜 مثل شعبي", callback_data=f"game_proverb_{user_id}"),
         InlineKeyboardButton(text="🎲 حظ", callback_data=f"game_luck_{user_id}")]
    ])
    sent = await message.reply("🎮 *اختر نوع اللعبة:*", reply_markup=kb, parse_mode="Markdown")
    # حذف الأزرار بعد 3 ثوانٍ
    asyncio.create_task(delete_after(sent, 3))

async def delete_after(msg, seconds):
    await asyncio.sleep(seconds)
    try:
        await msg.delete()
    except:
        pass

async def handle_game_callback(callback: CallbackQuery):
    """معالج الضغط على زر اللعبة (يتحقق من أن المستخدم نفسه)"""
    data = callback.data
    # تنسيق callback_data: game_{type}_{user_id}
    parts = data.split("_")
    if len(parts) != 3:
        await callback.answer("خطأ", show_alert=True)
        return
    game_type = parts[1]
    expected_user_id = int(parts[2])
    user_id = callback.from_user.id
    if user_id != expected_user_id:
        await callback.answer("هذه الأزرار ليست مخصصة لك!", show_alert=True)
        return
    await callback.answer("جاري تحضير اللعبة...")
    # بدء اللعبة
    await start_game(callback.message, game_type, user_id)
    # حذف رسالة الأزرار
    await callback.message.delete()

async def start_game(message: Message, game_type: str, user_id: int):
    chat_id = message.chat.id
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
    # حفظ الجلسة في قاعدة البيانات (اختياري)
    await save_game_session(chat_id, sent.message_id, game['type'], game['question'], game['answer'], prize, user_id)
    # جدولة حذف السؤال بعد 10 ثوانٍ إذا لم تتم الإجابة
    asyncio.create_task(delete_question_after_timeout(user_id, sent.message_id, chat_id, game['answer']))

async def delete_question_after_timeout(user_id, msg_id, chat_id, correct_answer):
    await asyncio.sleep(GAME_TIME_LIMIT)
    if user_id in active_games and active_games[user_id].get("message_id") == msg_id:
        # إزالة الجلسة
        active_games.pop(user_id, None)
        await send_auto_delete(chat_id, f"⏰ انتهت المهلة! الإجابة الصحيحة: {correct_answer}", delay=10)
        try:
            await bot.delete_message(chat_id, msg_id)
        except:
            pass

async def handle_game_answer(message: Message):
    """معالجة إجابة المستخدم (يجب أن يرد على رسالة السؤال)"""
    if not message.reply_to_message:
        return
    user_id = message.from_user.id
    if user_id not in active_games:
        return
    game = active_games[user_id]
    # التحقق من أن الرد كان على رسالة السؤال نفسها
    if message.reply_to_message.message_id != game["message_id"]:
        return
    user_answer = message.text.strip().lower()
    correct = game['correct_answer'].strip().lower()
    chat_id = game['chat_id']
    question_msg_id = game['message_id']

    if user_answer == correct:
        # إجابة صحيحة
        await update_user_money(user_id, game['prize'], "فوز بلعبة", None)
        await add_xp(user_id, 25, chat_id, message.from_user.full_name)
        result_text = f"🎉 <b>إجابة صحيحة!</b>\n💰 +{game['prize']} {CURRENCY_NAME}\n⭐ +25 XP"
        await send_auto_delete(chat_id, result_text, delay=10, parse_mode="HTML")
    else:
        result_text = f"❌ <b>إجابة خاطئة!</b>\nالإجابة الصحيحة هي: {correct}"
        await send_auto_delete(chat_id, result_text, delay=10, parse_mode="HTML")

    # حذف سؤال اللعبة وإجابة المستخدم
    try:
        await bot.delete_message(chat_id, question_msg_id)
        await message.delete()
    except:
        pass
    # إزالة الجلسة النشطة
    active_games.pop(user_id, None)

def register_games_handlers(dp: Dispatcher):
    dp.message.register(handle_game_answer)
    dp.callback_query.register(handle_game_callback, lambda c: c.data and c.data.startswith("game_"))
