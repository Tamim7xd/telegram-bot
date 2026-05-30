from aiogram import Bot, Dispatcher
from config import CURRENCY_NAME, LEVELUP_BONUS_MONEY, LEVELUP_BONUS_XP
from _core.xp import get_xp_progress
import asyncio

bot = None

def set_bot_instance(b: Bot):
    global bot
    bot = b

async def send_auto_delete(chat_id: int, text: str, parse_mode: str = "Markdown"):
    msg = await bot.send_message(chat_id, text, parse_mode=parse_mode)
    asyncio.create_task(delete_after(msg, 30))

async def delete_after(msg, seconds: int):
    await asyncio.sleep(seconds)
    try:
        await msg.delete()
    except:
        pass

async def send_levelup_notification(chat_id: int, user_id: int, new_level: int, user_name: str):
    progress = await get_xp_progress(user_id)
    text = f"""╭━━━━━━━━━━━━━━━━━━━━━━━━━━╮
┃ 🎉 *تـهـنـئـة* 🎉
╰━━━━━━━━━━━━━━━━━━━━━━━━━━╯

✨ *مبروك يا {user_name}* ✨
لقد وصلت إلى 🔥 *المستوى {new_level}* 🔥

💰 *مكافأة الترقية:* {LEVELUP_BONUS_MONEY} {CURRENCY_NAME}
⭐ *XP إضافي:* {LEVELUP_BONUS_XP} نقطة

📊 *شريط XP الجديد:*
{progress['bar']} {progress['percent']}%

📌 *المتبقي للمستوى التالي:* {progress['remaining']} XP"""
    await send_auto_delete(chat_id, text)

def register_notify_handlers(dp: Dispatcher):
    pass
