from aiogram import Dispatcher, Bot
from aiogram.filters import CommandStart, Command

from _core.events import (
    handle_admin_commands,
    handle_member_commands,
    add_xp_on_message
)

from _core.commands import cmd_start, cmd_adminiq


def setup_bot(dp: Dispatcher):

    # أوامر أساسية
    dp.message.register(cmd_start, CommandStart())
    dp.message.register(cmd_adminiq, Command("adminiq"))

    # أوامر الإدارة
    dp.message.register(handle_admin_commands, lambda m: m.text and m.text.startswith("$"))

    # أوامر الأعضاء
    dp.message.register(handle_member_commands, lambda m: m.text and m.text.startswith("#"))

    # XP system
    dp.message.register(add_xp_on_message)
