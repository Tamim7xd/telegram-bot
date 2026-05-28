from db import c, conn
from config import ADMIN_ID

def create_user(uid, name):
    c.execute("SELECT user_id FROM users WHERE user_id=?", (uid,))
    if c.fetchone():
        return

    c.execute("INSERT INTO users (user_id, name) VALUES (?,?)", (uid, name))
    conn.commit()


def get_user(uid):
    c.execute("SELECT * FROM users WHERE user_id=?", (uid,))
    return c.fetchone()


def add_message(uid):
    c.execute("UPDATE users SET messages = messages + 1 WHERE user_id=?", (uid,))
    conn.commit()


def add_money(uid, amount):
    c.execute("UPDATE users SET money = money + ? WHERE user_id=?", (amount, uid))
    conn.commit()


def remove_money(uid, amount):
    c.execute("UPDATE users SET money = MAX(money - ?, 0) WHERE user_id=?", (amount, uid))
    conn.commit()


def add_xp(uid, amount):
    c.execute("SELECT xp, level FROM users WHERE user_id=?", (uid,))
    xp, level = c.fetchone()

    xp += amount

    while xp >= level * 200:
        xp -= level * 200
        level += 1

        c.execute("UPDATE users SET level=?, xp=?, title=? WHERE user_id=?",
                  (level, xp, f"نجم ⭐ {level}", uid))
    else:
        c.execute("UPDATE users SET xp=?, level=? WHERE user_id=?",
                  (xp, level, uid))

    conn.commit()


def is_admin(uid):
    return uid == ADMIN_ID
