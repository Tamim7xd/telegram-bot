from aiogram import Dispatcher
from aiogram.types import CallbackQuery
from _core.games import start_game


async def callback_handler(callback: CallbackQuery, bot):

    data = callback.data

    if data == "game_math":
        await start_game(callback.message.chat.id, "math", bot)

    if data == "game_riddles":
        await start_game(callback.message.chat.id, "riddles", bot)

    await callback.answer()


def register_callbacks(dp: Dispatcher, bot):
    dp.callback_query.register(lambda c: callback_handler(c, bot))
