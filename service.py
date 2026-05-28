from db import c, conn

# =========================
# جلب مستخدم
# =========================
def get_user(uid: int):
    c.execute("SELECT * FROM users WHERE user_id=?", (uid,))
    return c.fetchone()


# =========================
# إنشاء مستخدم إذا غير موجود
# =========================
def create_user(uid: int, name: str):
    c.execute("SELECT user_id FROM users WHERE user_id=?", (uid,))
    if c.fetchone():
        return

    c.execute("""
        INSERT INTO users (user_id, name)
        VALUES (?, ?)
    """, (uid, name))

    conn.commit()


# =========================
# تحديث الرسائل
# =========================
def add_message(uid: int):
    c.execute("""
        UPDATE users
        SET messages = messages + 1
        WHERE user_id=?
    """, (uid,))
    conn.commit()
