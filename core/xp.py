from db import c, conn


# =========================
# ⭐ ADD XP SYSTEM
# =========================
def add_xp(uid, amount=25):

    c.execute("SELECT xp, level FROM users WHERE user_id=?", (uid,))
    row = c.fetchone()

    if not row:
        return 0, 1

    xp, level = row

    xp += amount
    needed = level * 100

    leveled_up = False

    if xp >= needed:
        level += 1
        xp = 0
        leveled_up = True

        # مكافأة عند الترقي
        c.execute("""
            UPDATE users
            SET level=?, xp=?, money = money + 250
            WHERE user_id=?
        """, (level, xp, uid))

    else:
        c.execute("""
            UPDATE users
            SET xp=?, level=?
            WHERE user_id=?
        """, (xp, level, uid))

    conn.commit()

    return xp, level, leveled_up


# =========================
# 📊 PROGRESS SYSTEM
# =========================
def get_progress(uid):

    c.execute("SELECT xp, level FROM users WHERE user_id=?", (uid,))
    row = c.fetchone()

    if not row:
        return 0, 1, 100, 0, "░░░░░░░░░░"

    xp, level = row

    needed = level * 100
    percent = int((xp / needed) * 100)

    if percent > 100:
        percent = 100

    bar = "█" * (percent // 10) + "░" * (10 - percent // 10)

    return xp, level, needed, percent, bar
