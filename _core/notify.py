from aiogram import Bot, Dispatcher
from config import CURRENCY_NAME, LEVELUP_BONUS_MONEY, LEVELUP_BONUS_XP
from _core.xp import get_xp_progress

bot = None

def set_bot_instance(b: Bot):
    global bot
    bot = b

async def send_levelup_notification(chat_id: int, user_id: int, new_level: int, user_name: str):
    progress = await get_xp_progress(user_id)
    text = f"""╭━━━━━━━━━━━━━━━╮
┃ 🎉  تـهـنـئـة  🎉
╰━━━━━━━━━━━━━━━╯

✨ *مبروك يا {user_name}* ✨

لقد وصلت إلى 🔥 *المستوى {new_level}* 🔥

━━━━━━━━━━━━━━━
💰 *مكافأة الترقية:* {LEVELUP_BONUS_MONEY} {CURRENCY_NAME}
⭐ *XP إضافي:* {LEVELUP_BONUS_XP} نقطة
━━━━━━━━━━━━━━━

📊 *شريط XP الجديد:*
{progress['bar']} {progress['percent']}%

📌 *المتبقي للمستوى التالي:* {progress['remaining']} XP
"""
    await bot.send_message(chat_id, text, parse_mode="Markdown")

async def send_money_notification(user_id: int, amount: int, reason: str, admin_name: str):
    text = f"""╭━━━━━━━━━━━━━━━╮
┃ 💰  إيـداع  💰
╰━━━━━━━━━━━━━━━╯

تم إضافة 💵 *{amount} {CURRENCY_NAME}* إلى رصيدك.

📝 *السبب:* {reason}

━ ━ ━ ━ ━ ━ ━ ━ ━
👤 بواسطة: {admin_name}
"""
    await bot.send_message(user_id, text, parse_mode="Markdown")

def register_notify_handlers(dp: Dispatcher):
    pass
