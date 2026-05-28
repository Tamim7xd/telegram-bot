from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, ChatPermissions
from telegram.ext import ContextTypes

from db import c, conn

# =========================
# إعداد الأدمن
# =========================
ADMIN_ID = 1007010982


# =========================
# USERS SYSTEM
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


def get_user(uid: int):
    c.execute("SELECT * FROM users WHERE user_id=?", (uid,))
    return c.fetchone()


def add_message(uid: int):
    c.execute("UPDATE users SET messages = messages + 1 WHERE user_id=?", (uid,))
    conn.commit()


def add_xp(uid: int, amount: int):
    c.execute("SELECT xp, level FROM users WHERE user_id=?", (uid,))
    row = c.fetchone()
    if not row:
        return

    xp, level = row
    xp += amount

    while xp >= level * 200:
        xp -= level * 200
        level += 1

        c.execute("""
            UPDATE users
            SET xp=?, level=?, title=?
            WHERE user_id=?
        """, (xp, level, f"نجم ⭐ {level}", uid))

    c.execute("""
        UPDATE users
        SET xp=?, level=?
        WHERE user_id=?
    """, (xp, level, uid))

    conn.commit()


# =========================
# ADMIN CHECK
# =========================
def is_admin(user_id: int):
    return user_id == ADMIN_ID


# =========================
# CALLBACK HANDLER (MAIN CORE)
# =========================
async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    data = query.data
    user = query.from_user

    # منع غير الأدمن
    if not is_admin(user.id):
        await query.answer("❌ ليس لديك صلاحية", show_alert=True)
        return

    # =========================
    # لوحة الأدمن
    # =========================
    if data == "admin":

        keyboard = [
            [InlineKeyboardButton("👥 المستخدمين", callback_data="admin_users")],
            [InlineKeyboardButton("🏆 الترتيب", callback_data="admin_top")],
            [InlineKeyboardButton("📊 الإحصائيات", callback_data="admin_stats")]
        ]

        await query.edit_message_text(
            "🛠 لوحة الأدمن",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    # =========================
    # USERS LIST
    # =========================
    elif data == "admin_users":

        c.execute("SELECT user_id, name FROM users LIMIT 20")
        users = c.fetchall()

        keyboard = [
            [InlineKeyboardButton(u[1], callback_data=f"admin_user:{u[0]}")]
            for u in users
        ]

        keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="admin")])

        await query.edit_message_text(
            "👥 المستخدمين",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    # =========================
    # USER PROFILE
    # =========================
    elif data.startswith("admin_user:"):

        uid = int(data.split(":")[1])
        u = get_user(uid)

        await query.edit_message_text(f"""
👤 ملف المستخدم

🆔 {u[0]}
👤 {u[1]}
💰 المال: {u[3]}
📨 الرسائل: {u[2]}
⭐ المستوى: {u[5]}
🔥 XP: {u[4]}
🏆 {u[6]}
""",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("💰 إضافة", callback_data=f"add:{uid}"),
                InlineKeyboardButton("💸 خصم", callback_data=f"rem:{uid}")
            ],
            [
                InlineKeyboardButton("🏆 لقب", callback_data=f"title:{uid}")
            ],
            [
                InlineKeyboardButton("🔇 كتم", callback_data=f"mute:{uid}"),
                InlineKeyboardButton("🚫 حظر", callback_data=f"ban:{uid}")
            ],
            [
                InlineKeyboardButton("🔙 رجوع", callback_data="admin_users")
            ]
        ]))

    # =========================
    # STATS
    # =========================
    elif data == "admin_stats":

        c.execute("SELECT COUNT(*) FROM users")
        users = c.fetchone()[0]

        c.execute("SELECT SUM(messages) FROM users")
        messages = c.fetchone()[0] or 0

        c.execute("SELECT SUM(money) FROM users")
        money = c.fetchone()[0] or 0

        await query.edit_message_text(f"""
📊 الإحصائيات

👥 المستخدمين: {users}
📨 الرسائل: {messages}
💰 الأموال: {money}
""",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 رجوع", callback_data="admin")]
        ]))

    # =========================
    # TOP USERS
    # =========================
    elif data == "admin_top":

        c.execute("""
            SELECT name, xp, level
            FROM users
            ORDER BY xp DESC
            LIMIT 10
        """)
        top = c.fetchall()

        text = "🏆 أفضل اللاعبين:\n\n"

        for i, u in enumerate(top, 1):
            text += f"{i}- {u[0]} | XP: {u[1]} | LVL: {u[2]}\n"

        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 رجوع", callback_data="admin")]
            ])
        )
