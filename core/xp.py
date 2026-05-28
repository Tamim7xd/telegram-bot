from db import c, conn
from core.titles import TITLES

def add_xp(uid, amount=25):

    c.execute("UPDATE users SET xp = xp + ? WHERE user_id=?", (amount, uid))

    c.execute("SELECT xp, level FROM users WHERE user_id=?", (uid,))
    xp, level = c.fetchone()

    needed = level * 100

    if xp >= needed:
        level += 1
        xp = 0

        c.execute("""
            UPDATE users
            SET level=?, xp=?, money = money + 250
            WHERE user_id=?
        """, (level, xp, uid))

    conn.commit()
    return xp, level


def get_progress(uid):

    c.execute("SELECT xp, level FROM users WHERE user_id=?", (uid,))
    xp, level = c.fetchone()

    needed = level * 100
    percent = int((xp / needed) * 100)

    bar = "█" * (percent // 10) + "░" * (10 - percent // 10)

    return xp, level, needed, percent, bar
