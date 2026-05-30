from aiogram import Bot, Dispatcher
import asyncio
from config import CURRENCY_NAME

bot = None

def set_bot_instance(b: Bot):
    global bot
    bot = b

def get_bot():
    if bot is None:
        raise RuntimeError("Bot not initialized")
    return bot


async def send_auto_delete(chat_id: int, text: str, parse_mode="Markdown"):
    b = get_bot()
    msg = await b.send_message(chat_id, text, parse_mode=parse_mode)
    asyncio.create_task(delete_after(msg, 30))


async def delete_after(msg, seconds: int):
    await asyncio.sleep(seconds)
    try:
        await msg.delete()
    except:
        pass


def register_notify_handlers(dp: Dispatcher):
    pass
