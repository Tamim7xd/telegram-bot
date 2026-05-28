from db import c, conn


# =========================
# إنشاء مستخدم
# =========================
def create_user(uid: int, name: str):
    c.execute("SELECT user_id FROM users WHERE user_id=?", (uid,))
    if c.fetchone():
        return

    c.execute("""
        INSERT INTO users (
            user_id,
            name,
            messages,
            money,
            xp,
            level,
            title,
            banned,
            muted
        )
        VALUES (?, ?, 0, 0, 0, 1, 'مبتدئ', 0, 0)
    """, (uid, name))

    conn.commit()


# =========================
# جلب مستخدم
# =========================
def get_user(uid: int):
    c.execute("SELECT * FROM users WHERE user_id=?", (uid,))
    return c.fetchone()


# =========================
# زيادة الرسائل
# =========================
def add_message(uid: int):
    c.execute("""
        UPDATE users
        SET messages = messages + 1
        WHERE user_id=?
    """, (uid,))
    conn.commit()


# =========================
# إضافة فلوس
# =========================
def add_money(uid: int, amount: int):
    c.execute("""
        UPDATE users
        SET money = money + ?
        WHERE user_id=?
    """, (amount, uid))
    conn.commit()


# =========================
# خصم فلوس
# =========================
def remove_money(uid: int, amount: int):
    c.execute("""
        UPDATE users
        SET money = CASE 
            WHEN money - ? < 0 THEN 0 
            ELSE money - ? 
        END
        WHERE user_id=?
    """, (amount, amount, uid))
    conn.commit()


# =========================
# إضافة XP + نظام مستوى تلقائي
# =========================
def add_xp(uid: int, amount: int):
    c.execute("SELECT xp, level FROM users WHERE user_id=?", (uid,))
    row = c.fetchone()

    if not row:
        return

    xp, level = row
    xp += amount

    # نظام الترقية
    while xp >= level * 200:
        xp -= level * 200
        level += 1

        # تحديث لقب بسيط حسب المستوى
        title = f"نجم ⭐ {level}"

        c.execute("""
            UPDATE users
            SET xp=?, level=?, title=?
            WHERE user_id=?
        """, (xp, level, title, uid))
    else:
        c.execute("""
            UPDATE users
            SET xp=?, level=?
            WHERE user_id=?
        """, (xp, level, uid))

    conn.commit()


# =========================
# تغيير لقب
# =========================
def set_title(uid: int, title: str):
    c.execute("""
        UPDATE users
        SET title=?
        WHERE user_id=?
    """, (title, uid))
    conn.commit()


# =========================
# حظر
# =========================
def ban_user(uid: int):
    c.execute("""
        UPDATE users
        SET banned=1
        WHERE user_id=?
    """, (uid,))
    conn.commit()


# =========================
# فك حظر
# =========================
def unban_user(uid: int):
    c.execute("""
        UPDATE users
        SET banned=0
        WHERE user_id=?
    """, (uid,))
    conn.commit()


# =========================
# كتم
# =========================
def mute_user(uid: int):
    c.execute("""
        UPDATE users
        SET muted=1
        WHERE user_id=?
    """, (uid,))
    conn.commit()


# =========================
# فك كتم
# =========================
def unmute_user(uid: int):
    c.execute("""
        UPDATE users
        SET muted=0
        WHERE user_id=?
    """, (uid,))
    conn.commit()


# =========================
# أفضل المستخدمين
# =========================
def top_users(limit=10):
    c.execute("""
        SELECT user_id, name, xp, level
        FROM users
        ORDER BY xp DESC
        LIMIT ?
    """, (limit,))

    return c.fetchall()
