from aiogram import Dispatcher
from aiogram.types import Message

from config import ADMIN_IDS, CURRENCY_NAME, XP_PER_MESSAGE
from _core.users import (
    update_user_money,
    get_user,
    set_user_status,
    get_or_create_user,
    is_admin,
    is_general_mod,
    add_general_mod,
    remove_general_mod
)

from _core.xp import add_xp, get_xp_progress
from _core.titles import set_user_title
from _core.notify import send_auto_delete
from db import db
import asyncio
from datetime import datetime
# lazy import لتجنب import error
def get_cmd_game():
    from _core.games import cmd_game
    return cmd_game

# =====================
# ADMIN COMMANDS (بدون حذف أي وظيفة)
# =====================
async def handle_admin_commands(message: Message):
    if not message.reply_to_message:
        return

    uid = message.from_user.id

    if not await is_admin(uid) and not await is_general_mod(uid):
        return

    target = message.reply_to_message.from_user
    text = message.text.strip()

    if text.startswith("$معلومات"):
        user = await get_user(target.id)
        if user:
            await message.reply(
                f"👤 {user['full_name']}\n💰 {user['money']}\n⭐ XP: {user['xp']}\n📊 LVL: {user['level']}"
            )


# =====================
# MEMBER COMMANDS (كل الخصائص محفوظة)
# =====================
async def handle_member_commands(message: Message):
    text = message.text.strip()
    uid = message.from_user.id

    await get_or_create_user(message.from_user)

    # 👤 الملف
    if text in ["#ملفي", "#حسابي", "#معلوماتي"]:
        user = await get_user(uid)
        xp = await get_xp_progress(uid)

        msg = await message.reply(
            f"""👤 {user['full_name']}
💰 {user['money']} {CURRENCY_NAME}
⭐ XP: {user['xp']}
📊 المستوى: {user['level']}
🏷️ {user['title'] or 'لا يوجد'}
📈 {xp['bar']} {xp['percent']}%"""
        )
        asyncio.create_task(delete_after(msg, 20))
        await message.delete()

    # 🎮 الألعاب
    elif text in ["#لعبة", "#العب", "#العاب"]:
        await get_cmd_game()(message)

    # 💰 المال
    elif text in ["#فلوس", "#فلوسي"]:
        user = await get_user(uid)
        await message.reply(f"💰 {user['money']} {CURRENCY_NAME}")

    # 🏷️ اللقب
    elif text in ["#لقب", "#لقبي"]:
        user = await get_user(uid)
        await message.reply(f"🏷️ {user['title'] or 'لا يوجد'}")

    # 📊 المستوى
    elif text in ["#مستواي", "#نقاطي"]:
        xp = await get_xp_progress(uid)
        await message.reply(f"📊 {xp['level']}\n{xp['bar']} {xp['percent']}%")


# =====================
# XP SYSTEM (بدون تعديل منطقك)
# =====================
async def add_xp_on_message(message: Message):
    await get_or_create_user(message.from_user)

    if not message.text:
        return

    if message.text.startswith(("#", "$")):
        return

    if await is_admin(message.from_user.id):
        return

    await add_xp(
        message.from_user.id,
        XP_PER_MESSAGE,
        message.chat.id,
        message.from_user.full_name
    )


# =====================
# DELETE HELPER
# =====================
async def delete_after(msg, seconds: int):
    await asyncio.sleep(seconds)
    try:
        await msg.delete()
    except:
        pass


# =====================
# REGISTER (بدون حذف أي handler)
# =====================
def register_event_handlers(dp: Dispatcher):
    dp.message.register(handle_admin_commands, lambda m: m.text and m.text.startswith("$"))
    dp.message.register(handle_member_commands, lambda m: m.text and m.text.startswith("#"))
    dp.message.register(add_xp_on_message)
