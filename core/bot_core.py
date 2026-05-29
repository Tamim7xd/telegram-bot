from aiogram import Dispatcher, types
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from _core.users import get_or_create_user
from _core.xp import add_xp
from _core.games import cmd_game  # for #لعبة
from _core.events import handle_hashtag_commands
import re

async def cmd_start(message: Message):
    user = await get_or_create_user(message.from_user)
    await message.answer(f"✨ أهلاً بك {user['full_name']} في البوت المتكامل!\nاكتب #ملفي لعرض بياناتك، أو #لعبة للبدء.")

async def cmd_adminiq(message: Message):
    from _core.callbacks import admin_panel
    await admin_panel(message)

async def handle_hashtag_root(message: Message):
    text = message.text.strip()
    if text.startswith("#"):
        await handle_hashtag_commands(message)

def setup_bot(dp: Dispatcher):
    dp.message.register(cmd_start, CommandStart())
    dp.message.register(cmd_adminiq, Command("adminiq"))
    dp.message.register(handle_hashtag_root)
