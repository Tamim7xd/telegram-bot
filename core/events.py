from core.users import add_xp
from core.games import reward


# =========================
# رسالة مستخدم
# =========================
def on_message(user_id: int):
    add_xp(user_id, 10)


# =========================
# فوز لعبة
# =========================
def on_game_win(user_id: int):
    r = reward()

    add_xp(user_id, r["xp"])

    return r
