from aiogram import Dispatcher
from aiogram.types import Message
from config import ADMIN_IDS, CURRENCY_NAME
from _core.users import get_user, update_user_money
from _core.notify import send_auto_delete

async def dollar_commands(message: Message):
    if not message.reply_to_message:
        return
    uid = message.from_user.id
    if uid not in ADMIN_IDS:
        return
    target = message.reply_to_message.from_user
    text = message.text.strip()
    chat_id = message.chat.id
    target_name = target.full_name

    if text.startswith("$خصم"):
        parts = text.split()
        if len(parts) >= 2 and parts[1].isdigit():
            amt = int(parts[1])
            reason = " ".join(parts[2:]) if len(parts) > 2 else "خصم"
            await update_user_money(target.id, -amt, reason, uid)
            await send_auto_delete(chat_id, f"✅ خصم {amt} من {target_name}\nالسبب: {reason}")
        else:
            await send_auto_delete(chat_id, "❌ استخدم: $خصم 50 سبب")
    elif text.startswith("$اختبار"):
        await send_auto_delete(chat_id, "✅ أمر $ يعمل")

async def hash_commands(message: Message):
    text = message.text.strip()
    if text.startswith("#اختبار"):
        await send_auto_delete(message.chat.id, "✅ أمر # يعمل")

async def add_xp_handler(message: Message):
    # لا تفعل شيئاً حالياً
    pass

def register_event_handlers(dp: Dispatcher):
    dp.message.register(dollar_commands, lambda m: m.text and m.text.startswith("$"))
    dp.message.register(hash_commands, lambda m: m.text and m.text.startswith("#"))
    dp.message.register(add_xp_handler)
