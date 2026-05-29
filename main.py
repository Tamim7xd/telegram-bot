from aiogram import Bot, Dispatcher
from config import BOT_TOKEN

from _core.notify import set_bot_instance
from _core.bot_core import setup_bot

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

set_bot_instance(bot)

setup_bot(dp)
