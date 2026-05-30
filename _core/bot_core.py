from _core.events import handle_text
from _core.games import callbacks as game_callbacks
from _core.notify import set_bot


def register_core(dp, bot):
    """
    تسجيل جميع أجزاء البوت بشكل صحيح (aiogram v3)
    """

    # 🔗 ربط البوت بالأنظمة الداخلية
    set_bot(bot)

    # =========================
    # 🎮 Callback Queries (الأزرار)
    # =========================
    dp.callback_query.register(game_callbacks)

    # =========================
    # 💬 جميع الرسائل النصية
    # =========================
    dp.message.register(handle_text)
