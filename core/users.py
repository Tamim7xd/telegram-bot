from db import c, conn
from core.xp import level_up, need_xp
from core.titles import TITLES


def add_xp(user_id, amount):
    c.execute("SELECT xp, level FROM users WHERE user_id=?", (user_id,))
    row = c.fetchone()

    if not row:
        return

    xp, level = row
    xp += amount

    level, xp, title = level_up(level, xp, TITLES)

    c.execute("""
        UPDATE users
        SET xp=?, level=?, title=?
        WHERE user_id=?
    """, (xp, level, title, user_id))

    conn.commit()
