from shared.message_builder import send_and_delete
from .notifications_data import build_notification

async def send_warning(context, chat_id, user_name, reason, warnings_count, admin_name):
    text = build_notification("تحذير", "⚠️", f"👤 {user_name}\n📝 {reason}\n🔢 {warnings_count}", admin_name)
    await send_and_delete(context, chat_id, text, timeout=5)

async def send_mute(context, chat_id, user_name, duration, reason, admin_name):
    text = build_notification("كتم", "🔇", f"👤 {user_name}\n⏱️ {duration}\n📝 {reason}", admin_name)
    await send_and_delete(context, chat_id, text, timeout=5)