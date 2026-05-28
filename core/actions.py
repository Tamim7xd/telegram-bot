from db import c, conn

def add_money(uid, amount):
    c.execute("UPDATE users SET money = money + ? WHERE user_id=?", (amount, uid))
    conn.commit()

def remove_money(uid, amount):
    c.execute("UPDATE users SET money = money - ? WHERE user_id=?", (amount, uid))
    conn.commit()

def set_title(uid, title):
    c.execute("UPDATE users SET title=? WHERE user_id=?", (title, uid))
    conn.commit()

def mute(uid):
    c.execute("UPDATE users SET muted=1 WHERE user_id=?", (uid,))
    conn.commit()

def unmute(uid):
    c.execute("UPDATE users SET muted=0 WHERE user_id=?", (uid,))
    conn.commit()

def ban(uid):
    c.execute("UPDATE users SET banned=1 WHERE user_id=?", (uid,))
    conn.commit()

def unban(uid):
    c.execute("UPDATE users SET banned=0 WHERE user_id=?", (uid,))
    conn.commit()
