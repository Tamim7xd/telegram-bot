from db import c, conn

def xp_add(uid, amount):
    c.execute("SELECT xp, level FROM users WHERE user_id=?", (uid,))
    xp, level = c.fetchone()

    xp += amount
    leveled = False

    while xp >= level * 100:
        xp -= level * 100
        level += 1
        leveled = True

    c.execute("UPDATE users SET xp=?, level=? WHERE user_id=?", (xp, level, uid))
    conn.commit()

    return leveled, level


def get_progress(uid):
    c.execute("SELECT xp, level FROM users WHERE user_id=?", (uid,))
    xp, level = c.fetchone()

    need = level * 100
    percent = int((xp / need) * 100)

    bar = "█" * (percent // 10) + "░" * (10 - percent // 10)

    return xp, level, need, percent, bar
