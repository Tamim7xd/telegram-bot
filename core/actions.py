from db import c, conn
from core.users import register


# ─────────────────────────────
# 🧠 ضمان وجود المستخدم
# ─────────────────────────────
def ensure_user(uid):
    register(type("U", (), {"id": uid, "first_name": "user"}))


# ─────────────────────────────
# 💰 إضافة فلوس
# ─────────────────────────────
def add_money(uid, amount):
    ensure_user(uid)

    c.execute("""
        UPDATE users
        SET money = money + ?
        WHERE user_id = ?
    """, (amount, uid))

    conn.commit()


# ─────────────────────────────
# 💸 خصم فلوس
# ─────────────────────────────
def remove_money(uid, amount):
    ensure_user(uid)

    c.execute("""
        UPDATE users
        SET money = money - ?
        WHERE user_id = ?
    """, (amount, uid))

    conn.commit()


# ─────────────────────────────
# 🔇 كتم المستخدم
# ─────────────────────────────
def mute(uid):
    ensure_user(uid)

    c.execute("""
        UPDATE users
        SET muted = 1
        WHERE user_id = ?
    """, (uid,))

    conn.commit()


# ─────────────────────────────
# 🚫 حظر المستخدم
# ─────────────────────────────
def ban(uid):
    ensure_user(uid)

    c.execute("""
        UPDATE users
        SET banned = 1
        WHERE user_id = ?
    """, (uid,))

    conn.commit()


# ─────────────────────────────
# 🔓 فك الحظر
# ─────────────────────────────
def unban(uid):
    ensure_user(uid)

    c.execute("""
        UPDATE users
        SET banned = 0
        WHERE user_id = ?
    """, (uid,))

    conn.commit()


# ─────────────────────────────
# 🏆 تعديل اللقب
# ─────────────────────────────
def set_title(uid, title):
    ensure_user(uid)

    c.execute("""
        UPDATE users
        SET title = ?
        WHERE user_id = ?
    """, (title, uid))

    conn.commit()
