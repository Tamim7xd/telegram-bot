from db import conn, c


# =========================
# ADD MONEY
# =========================
def add_money(uid, amount):

    c.execute(
        "UPDATE users SET money = money + ? WHERE user_id=?",
        (amount, uid)
    )

    conn.commit()


# =========================
# REMOVE MONEY
# =========================
def remove_money(uid, amount):

    c.execute(
        "UPDATE users SET money = money - ? WHERE user_id=?",
        (amount, uid)
    )

    conn.commit()


# =========================
# TITLE
# =========================
def set_title(uid, title):

    c.execute(
        "UPDATE users SET title=? WHERE user_id=?",
        (title, uid)
    )

    conn.commit()


# =========================
# MUTE
# =========================
def mute(uid):

    c.execute(
        "UPDATE users SET muted=1 WHERE user_id=?",
        (uid,)
    )

    conn.commit()


# =========================
# UNMUTE
# =========================
def unmute(uid):

    c.execute(
        "UPDATE users SET muted=0 WHERE user_id=?",
        (uid,)
    )

    conn.commit()


# =========================
# BAN
# =========================
def ban(uid):

    c.execute(
        "UPDATE users SET banned=1 WHERE user_id=?",
        (uid,)
    )

    conn.commit()


# =========================
# UNBAN
# =========================
def unban(uid):

    c.execute(
        "UPDATE users SET banned=0 WHERE user_id=?",
        (uid,)
    )

    conn.commit()
