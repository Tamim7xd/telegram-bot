from _core.users import (
    get_user,
    update_user_money,
    set_user_status,
    get_user_role
)

from _core.notify import get_bot
from db import db
import time


# 👤 أعضاء
async def handle_member_commands(message):
    text = message.text
    user_id = message.from_user.id

    if not text:
        return

    if text in ["#ملفي", "#ملف", "#معلومات", "#معلوماتي"]:
        user = await get_user(user_id)
        await message.reply(f"👤 {user['full_name']} | 💰 {user['money']}")

    elif text in ["#لعبة", "#العب", "#العاب"]:
        from _core.games import cmd_game
        await cmd_game(message)


# 👮 إدارة
async def handle_admin_commands(message):

    text = message.text
    role = await get_user_role(message.from_user.id)

    if not text:
        return

    if not text.startswith("$"):
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
        duration = parts[1] if len(parts) > 1 else "30m"
        reason = parts[2] if len(parts) > 2 else "لا يوجد سبب"

        seconds = int(duration[:-1]) * 60 if duration.endswith("m") else 1800

        await message.chat.restrict_member(
            user_id=target_id,
            permissions={"can_send_messages": False}
        )

        await bot.send_message(chat_id, f"🔇 تم كتم {target_name}")

    # ⚠️ تحذير
    elif text.startswith("$تحذير"):
        reason = text.replace("$تحذير", "").strip()

        await db.execute("""
            INSERT INTO warnings (user_id, admin_id, admin_name, reason)
            VALUES ($1, $2, $3, $4)
        """, target_id, message.from_user.id, message.from_user.full_name, reason)

        await bot.send_message(chat_id, f"⚠️ تم تحذير {target_name}")

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

        await bot.send_message(chat_id, f"💰 تم خصم {amount} من {target_name}")


# ⭐ XP
async def add_xp_on_message(message):
    if not message.text:
        return

    if message.text.startswith("#") or message.text.startswith("$"):
        return

    from config import XP_PER_MESSAGE
    from _core.xp import add_xp

    await add_xp(message.from_user.id, XP_PER_MESSAGE, message.chat.id, message.from_user.full_name)
