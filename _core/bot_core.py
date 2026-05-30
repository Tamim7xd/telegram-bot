from aiogram import Dispatcher
from aiogram.filters import CommandStart, Command
from aiogram.types import Message

from _core.events import handle_text

async def start(message: Message):
    await message.answer("👋 أهلاً بك في البوت")

async def admin_cmd(message: Message):
    await message.answer("لوحة الأدمن")

def register_core(dp: Dispatcher, bot):

    dp.message.register(start, CommandStart())
    dp.message.register(admin_cmd, Command("adminiq"))

    # 🚨 مهم: هذا هو المعالج الوحيد للرسائل
    dp.message.register(handle_text)
