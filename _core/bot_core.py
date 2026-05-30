from _core.events import handle_text
from _core.games import register_games_handlers
from _core.notify import set_bot


def register_core(dp, bot):

    # ربط البوت
    set_bot(bot)

    # الرسائل
    dp.message.register(handle_text)

    # الألعاب (بدل callbacks)
    register_games_handlers(dp, bot)
