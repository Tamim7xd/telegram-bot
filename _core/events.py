import time
from aiogram.types import ChatPermissions

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


# 👮 إدارة كاملة (FIXED)
async def handle_admin_commands(message):

    text = message.text

    if not text:
        return

    # ❗ إصلاح مهم: لازم رد
    if not message.reply_to_message:
        return await message.reply("❌ لازم ترد على رسالة المستخدم")

    target = message.reply_to_message.from_user
    target_id = target.id
    target_name = target.full_name

    bot = get_bot()
    chat_id = message.chat.id

    # 🔇 كتم (FIXED)
    if text.startswith("$كتم"):

        parts = text.split(maxsplit=2)
        reason = parts[2] if len(parts) > 2 else "لا يوجد سبب"

        try:
            await message.chat.restrict(
                target_id,
                ChatPermissions(can_send_messages=False)
            )
        except:
            await message.bot.restrict_chat_member(
                chat_id,
                target_id,
                permissions=ChatPermissions(can_send_messages=False)
            )

        await bot.send_message(
            chat_id,
            f"🔇 تم كتم {target_name}\n📝 السبب: {reason}"
        )

    # ⚠️ تحذير
    elif text.startswith("$تحذير"):
        reason = text.replace("$تحذير", "").strip()

        await bot.send_message(
            chat_id,
            f"⚠️ تم تحذير {target_name}\n📝 السبب: {reason}"
        )

    # 🚫 حظر
    elif text.startswith("$حظر"):
        await set_user_status(target_id, "banned")

        try:
            await message.chat.ban_member(target_id)
        except:
            await message.bot.ban_chat_member(chat_id, target_id)

        await bot.send_message(
            chat_id,
            f"🚫 تم حظر {target_name}"
        )

    # 💰 خصم
    elif text.startswith("$خصم"):

        parts = text.split(maxsplit=2)

        if len(parts) < 2:
            return await message.reply("❌ استخدم: $خصم 100 سبب")

        try:
            amount = int(parts[1])
        except:
            return await message.reply("❌ المبلغ غير صحيح")

        reason = parts[2] if len(parts) > 2 else "لا يوجد سبب"

        await update_user_money(
            target_id,
            -amount,
            reason,
            message.from_user.id
        )

        await bot.send_message(
            chat_id,
            f"💰 تم خصم {amount} من {target_name}\n📝 السبب: {reason}"
        )


# ⭐ XP SYSTEM (FIXED)
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
