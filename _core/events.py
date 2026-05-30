from aiogram import Dispatcher
from aiogram.types import Message
from config import ADMIN_IDS
from _core.users import get_or_create_user
from _core.notify import send_auto_delete

# دوال الاختبار الأساسية
async def handle_member_commands(message: Message):
    """هذه الدالة التي يستوردها bot_core"""
    await get_or_create_user(message.from_user)
    text = message.text.strip()
    if text.startswith("#"):
        await send_auto_delete(message.chat.id, f"✅ تم استلام أمر #: {text}")

async def dollar_commands(message: Message):
    if message.text and message.text.startswith("$"):
        await send_auto_delete(message.chat.id, f"✅ تم استلام أمر $: {message.text}")

async def add_xp_handler(message: Message):
    pass  # للتجربة

def register_event_handlers(dp: Dispatcher):
    dp.message.register(dollar_commands, lambda m: m.text and m.text.startswith("$"))
    dp.message.register(handle_member_commands, lambda m: m.text and m.text.startswith("#"))
    dp.message.register(add_xp_handler)
