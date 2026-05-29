import random
import asyncio
from aiogram import Dispatcher
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from _core.game_engine import get_random_game, save_game_session, check_answer
from _core.users import update_user_money
from _core.xp import add_xp
from _core.notify import bot
from config import GAME_TIME_LIMIT, DEFAULT_GAME_PRIZE_MIN, DEFAULT_GAME_PRIZE_MAX, CURRENCY_NAME

# ========== أزرار أنواع الألعاب الـ 6 ==========
GAME_TYPES = {
    "puzzles": "🧠 لغز",
    "general_qa": "❓ سؤال عام",
    "mcq": "🔘 اختيار من متعدد",
    "speed_words": "⚡ سرعة",
    "proverbs": "📜 مثل شعبي",
    "luck_boxes": "🎲 حظ (صندوق)"
}

async def show_game_menu(message: Message):
    """عرض قائمة أزرار الألعاب"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    # صفين كل صف 3 أزرار
    row1 = [InlineKeyboardButton(text=GAME_TYPES["puzzles"], callback_data="game_puzzles"),
            InlineKeyboardButton(text=GAME_TYPES["general_qa"], callback_data="game_general"),
            InlineKeyboardButton(text=GAME_TYPES["mcq"], callback_data="game_mcq")]
    row2 = [InlineKeyboardButton(text=GAME_TYPES["speed_words"], callback_data="game_speed_words"),
            InlineKeyboardButton(text=GAME_TYPES["proverbs"], callback_data="game_proverbs"),
            InlineKeyboardButton(text=GAME_TYPES["luck_boxes"], callback_data="game_luck_boxes")]
    keyboard.inline_keyboard.append(row1)
    keyboard.inline_keyboard.append(row2)
    keyboard.inline_keyboard.append([InlineKeyboardButton(text="🎲 لعبة عشوائية", callback_data="game_random")])
    await message.reply("🎮 *اختر نوع اللعبة:*", reply_markup=keyboard, parse_mode="Markdown")

async def start_game(chat_id: int, game_type: str, prize: int):
    """بدء لعبة وإرسال السؤال"""
    game = await get_random_game(prize, game_type)
    if not game:
        await bot.send_message(chat_id, f"⚠️ لا توجد أسئلة لنوع '{game_type}' حالياً. أضف أسئلة في ملف data/{game_type}.json")
        return False
    sent_msg = await bot.send_message(chat_id, game['display_text'], parse_mode="Markdown")
    await save_game_session(chat_id, sent_msg.message_id, game['type'], game['question'], game['answer'], prize)
    asyncio.create_task(end_game_timeout(chat_id, sent_msg.message_id, game['answer']))
    return True

async def end_game_timeout(chat_id: int, msg_id: int, correct_answer: str):
    await asyncio.sleep(GAME_TIME_LIMIT)
    await bot.send_message(chat_id, f"⏰ *انتهت المهلة!*\nالإجابة الصحيحة: `{correct_answer}`", parse_mode="Markdown")

async def handle_game_answer(message: Message):
    """معالجة إجابة المستخدم (يجب أن يرد على رسالة اللعبة)"""
    if not message.reply_to_message:
        return
    result = await check_answer(message.chat.id, message.reply_to_message.message_id, message.text)
    if result is None:
        return
    prize = result
    if prize > 0:
        # إضافة 10 دينار (أو الجائزة الأصلية) – هنا نجعل الجائزة 10 دينار ثابتة
        fixed_prize = 10
        await update_user_money(message.from_user.id, fixed_prize, "فوز بلعبة", None)
        await add_xp(message.from_user.id, 25, message.chat.id, message.from_user.full_name)
        # إشعار متطور للمجموعة
        notification = f"""╭━━━━━━━━━━━━━━━━━━━━━━━━━━╮
┃ 🎉 *فـوز في اللـعبة* 🎉
╰━━━━━━━━━━━━━━━━━━━━━━━━━━╯

✨ *الفائز:* {message.from_user.full_name}
🎮 *نوع اللعبة:* {result['game_type'] if isinstance(result, dict) else 'لعبة'}
💰 *المكافأة:* {fixed_prize} {CURRENCY_NAME}
⭐ *نقاط الخبرة:* +25 XP

━━━━━━━━━━━━━━━━━━━━━━━━━━
إجابة صحيحة! أحسنت! 🎯"""
        await bot.send_message(message.chat.id, notification, parse_mode="Markdown")
    elif prize == 0:
        await message.reply("❌ *إجابة خاطئة!*", parse_mode="Markdown")

async def game_callback(callback: CallbackQuery):
    """معالج الضغط على زر اللعبة"""
    await callback.answer("جاري تحضير اللعبة...")
    game_type = callback.data.replace("game_", "")
    if game_type == "random":
        game_type = None
    prize = random.randint(DEFAULT_GAME_PRIZE_MIN, DEFAULT_GAME_PRIZE_MAX)
    await callback.message.delete()
    await start_game(callback.message.chat.id, game_type, prize)

async def cmd_game(message: Message):
    """الأمر #لعبة"""
    await show_game_menu(message)

def register_games_handlers(dp: Dispatcher):
    dp.message.register(cmd_game, lambda m: m.text and m.text in ["#لعبة", "#العب", "#العاب"])
    dp.message.register(handle_game_answer)
    dp.callback_query.register(game_callback, lambda c: c.data and c.data.startswith("game_"))
