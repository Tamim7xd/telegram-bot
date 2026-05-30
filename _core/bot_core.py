from aiogram import Dispatcher
from aiogram.filters import CommandStart, Command
from aiogram.types import Message

from _core.users import get_or_create_user
from _core.callbacks import admin_panel
from config import ADMIN_IDS


async def cmd_start(message: Message):
    user = await get_or_create_user(message.from_user)
    await message.answer(f"✨ أهلاً {user['full_name']}")


async def cmd_admin(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return await message.answer("⚠️ ليس لديك صلاحية")
    await admin_panel(message)


# =========================
# FIXED: منع circular import نهائياً
# =========================
def get_handle_member_commands():
    from _core.events import handle_member_commands
    return handle_member_commands


async def catch_all(message: Message):
    await get_or_create_user(message.from_user)

    if message.text and message.text.startswith("#"):
        handler = get_handle_member_commands()
        await handler(message)


def setup_bot(dp: Dispatcher):
    dp.message.register(cmd_start, CommandStart())
    dp.message.register(cmd_admin, Command("adminiq"))

    # مهم: هذا يعالج كل رسائل #
    dp.message.register(catch_all)
