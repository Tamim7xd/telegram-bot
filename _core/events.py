from aiogram import Dispatcher
from aiogram.types import Message
from config import ADMIN_IDS
from _core.users import get_or_create_user
from _core.notify import send_auto_delete

# ========== معالج الأوامر البسيط (للتأكد من العمل) ==========
async def handle_member_commands(message: Message):
    """هذه الدالة التي يستوردها bot_core"""
    await get_or_create_user(message.from_user)
    text = message.text.strip()
    if text.startswith("#"):
        await send_auto_delete(message.chat.id, f"✅ تم استلام أمر #: {text}")
    elif text.startswith("$"):
        await send_auto_delete(message.chat.id, f"✅ تم استلام أمر $: {text}")
    elif text.isdigit():
        await send_auto_delete(message.chat.id, f"✅ تم استلام رقم: {text}")

async def add_xp_handler(message: Message):
    pass

def register_event_handlers(dp: Dispatcher):
    dp.message.register(handle_member_commands)   # تسجيل كل الرسائل
    dp.message.register(add_xp_handler)
