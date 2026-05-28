from db import c, conn

# ─────────────────────────────
# ⭐ إضافة XP + مستوى
# ─────────────────────────────
def add_xp(uid, amount):

    c.execute("SELECT xp, level FROM users WHERE user_id=?", (uid,))
    row = c.fetchone()

    if not row:
        return False, 1

    xp, level = row

    xp += amount
    leveled_up = False

    while xp >= level * 100:
        xp -= level * 100
        level += 1
        leveled_up = True

    c.execute(
        "UPDATE users SET xp=?, level=? WHERE user_id=?",
        (xp, level, uid)
    )
    conn.commit()

    return leveled_up, level


# ─────────────────────────────
# 📊 شريط التقدم
# ─────────────────────────────
def get_progress(uid):

    c.execute("SELECT xp, level FROM users WHERE user_id=?", (uid,))
    row = c.fetchone()

    if not row:
        return 0, 1, 100, 0, ""

    xp, level = row

    need = level * 100
    percent = int((xp / need) * 100) if need else 0

    bar = "█" * (percent // 10) + "░" * (10 - percent // 10)

    return xp, level, need, percent, bar
