import time
from _core.notify import get_bot
from _core.users import (
    get_user,
    update_user_money,
    set_user_status,
    get_user_role
)

from config import XP_PER_MESSAGE
from _core.xp import add_xp


# 👤 أعضاء
async def handle_member_commands(message):

    text = message.text
    user_id = message.from_user.id

    if not text:
        return

    if text in ["#ملفي", "#ملف", "#معلومات", "#معلوماتي"]:
        user = await get_user(user_id)

        await message.reply(
            f"👤 الملف الشخصي\n"
            f"━━━━━━━━━━━━━━\n"
            f"💰 {user['money']}\n"
            f"⭐ {user['xp']}\n"
            f"🏆 {user['level']}"
        )

    elif text in ["#لعبة", "#العب", "#العاب"]:
        from _core.games import cmd_game
        await cmd_game(message)


# 👮 إدارة كاملة
async def handle_admin_commands(message):

    text = message.text

    if not text:
        return

    if not message.reply_to_message:
        return await message.reply("❌ لازم رد على المستخدم")

    target = message.reply_to_message.from_user
    target_id = target.id
    target_name = target.full_name

    bot = get_bot()
    chat_id = message.chat.id

    # 🔇 كتم
    if text.startswith("$كتم"):
        parts = text.split(maxsplit=2)
        reason = parts[2] if len(parts) > 2 else "لا يوجد سبب"

        await message.chat.restrict_member(
            user_id=target_id,
            permissions={"can_send_messages": False}
        )

        await bot.send_message(chat_id, f"🔇 تم كتم {target_name}\n📝 {reason}")

    # ⚠️ تحذير
    elif text.startswith("$تحذير"):
        reason = text.replace("$تحذير", "").strip()

        await bot.send_message(chat_id, f"⚠️ تم تحذير {target_name}\n📝 {reason}")

    # 🚫 حظر
    elif text.startswith("$حظر"):
        await set_user_status(target_id, "banned")
        await bot.send_message(chat_id, f"🚫 تم حظر {target_name}")

    # 💰 خصم
    elif text.startswith("$خصم"):
        parts = text.split(maxsplit=2)

        amount = int(parts[1]) if len(parts) > 1 else 0
        reason = parts[2] if len(parts) > 2 else "لا يوجد سبب"

        await update_user_money(target_id, -amount, reason, message.from_user.id)

        await bot.send_message(
            chat_id,
            f"💰 تم خصم {amount} من {target_name}"
        )


# ⭐ XP SYSTEM
async def add_xp_on_message(message):

    if not message.text:
        return

    if message.text.startswith("#") or message.text.startswith("$"):
        return

    await add_xp(
        message.from_user.id,
        XP_PER_MESSAGE,
        message.chat.id,
        message.from_user.full_name
    )
