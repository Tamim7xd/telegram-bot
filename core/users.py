from db import c, conn

def register(user):
    c.execute("SELECT user_id FROM users WHERE user_id=?", (user.id,))
    if not c.fetchone():
        c.execute(
            "INSERT INTO users(user_id, name) VALUES(?,?)",
            (user.id, user.first_name)
        )
        conn.commit()


def get(uid):
    c.execute("SELECT * FROM users WHERE user_id=?", (uid,))
    return c.fetchone()


def add_message(uid):
    c.execute("""
        UPDATE users
        SET messages = messages + 1,
            money = money + 250
        WHERE user_id=?
    """, (uid,))
    conn.commit()
