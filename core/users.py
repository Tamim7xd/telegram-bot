from db import c, conn
from core.titles import TITLES


def add_xp(uid: int, amount: int):
    c.execute("SELECT xp, level FROM users WHERE user_id=?", (uid,))
    row = c.fetchone()

    if not row:
        return

    xp, level = row
    xp += amount

    # الترقية
    while xp >= level * 200:
        xp -= level * 200
        level += 1

    title = TITLES[min(level - 1, len(TITLES) - 1)]

    c.execute("""
        UPDATE users
        SET xp=?, level=?, title=?
        WHERE user_id=?
    """, (xp, level, title, uid))

    conn.commit()
