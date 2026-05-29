from aiogram.types import Message
from _core.users import get_user


async def cmd_start(message: Message):
    user = await get_user(message.from_user.id)

    await message.answer(
        f"✨ أهلاً بك {message.from_user.full_name}\n"
        f"━━━━━━━━━━━━━━\n"
        f"💰 الرصيد: {user['money']}\n"
        f"⭐ XP: {user['xp']}\n"
        f"🏆 المستوى: {user['level']}\n"
        f"🏷 اللقب: {user['title'] or 'لا يوجد'}\n"
        f"━━━━━━━━━━━━━━\n"
        f"🎮 #لعبة لبدء اللعب"
    )


async def cmd_adminiq(message: Message):
    await message.answer(
        "👑 لوحة الإدارة\n"
        "━━━━━━━━━━━━━━\n"
        "⚙️ النظام يعمل بشكل مستقر\n"
        "📌 الأوامر:\n"
        "$كتم (بالرد)\n"
        "$تحذير (بالرد)\n"
        "$خصم (بالرد)\n"
        "$حظر (بالرد)"
    )
