from aiogram import Dispatcher
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from _core.users import get_or_create_user
from _core.events import handle_member_commands

async def cmd_start(message: Message):
    user = await get_or_create_user(message.from_user)
    await message.answer(f"✨ أهلاً {user['full_name']}!\n#ملفي لعرض بياناتك، #لعبة للبدء.")

async def cmd_adminiq(message: Message):
    from _core.callbacks import admin_panel
    await admin_panel(message)

async def catch_all(message: Message):
    await get_or_create_user(message.from_user)
    if message.text and message.text.startswith("#"):
        await handle_member_commands(message)

def setup_bot(dp: Dispatcher):
    dp.message.register(cmd_start, CommandStart())
    dp.message.register(cmd_adminiq, Command("adminiq"))
    dp.message.register(catch_all)
