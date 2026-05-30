from aiogram import Dispatcher
from aiogram.types import Message
from config import ADMIN_IDS
from _core.users import get_or_create_user

# معالج لكل الرسائل (للتأكد من استقبالها)
async def catch_all(message: Message):
    await get_or_create_user(message.from_user)
    text = message.text or ""
    if text.startswith("#"):
        await message.reply(f"✅ أمر #: {text}")
    elif text.startswith("$"):
        await message.reply(f"✅ أمر $: {text}")
    elif text.isdigit():
        await message.reply(f"✅ رقم: {text}")
    else:
        # رسالة عادية
        await message.reply(f"رسالة عادية: {text}")

def register_event_handlers(dp: Dispatcher):
    dp.message.register(catch_all)
