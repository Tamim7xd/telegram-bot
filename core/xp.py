from db import c, conn
from core.titles import TITLES

def add_xp(uid, amount=25):

    c.execute("SELECT xp, level FROM users WHERE user_id=?", (uid,))
    xp, level = c.fetchone()

    xp += amount
    needed = level * 250

    leveled_up = False

    if xp >= needed:
        xp = xp - needed
        level += 1
        leveled_up = True

    title = TITLES[min(level, len(TITLES)-1)]

    c.execute("""
        UPDATE users
        SET xp=?, level=?, title=?
        WHERE user_id=?
    """, (xp, level, title, uid))

    conn.commit()

    return xp, level, needed, leveled_up
