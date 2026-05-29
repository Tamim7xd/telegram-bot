from aiogram import Dispatcher
from aiogram.filters import CommandStart, Command

from _core.commands import cmd_start, cmd_adminiq
from _core.events import handle_admin_commands, handle_member_commands, add_xp_on_message


def setup_bot(dp: Dispatcher):

    dp.message.register(cmd_start, CommandStart())
    dp.message.register(cmd_adminiq, Command("adminiq"))

    dp.message.register(handle_admin_commands, lambda m: m.text and m.text.startswith("$"))
    dp.message.register(handle_member_commands, lambda m: m.text and m.text.startswith("#"))

    dp.message.register(add_xp_on_message)
