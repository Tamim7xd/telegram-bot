from db import execute, fetchone

async def get_user(uid):
    row = fetchone("SELECT * FROM users WHERE telegram_id=?", (uid,))
    return row

async def create_user(user):
    execute(
        "INSERT OR IGNORE INTO users (telegram_id, username, full_name) VALUES (?, ?, ?)",
        (user.id, user.username, user.full_name)
    )

async def add_money(uid, amount):
    execute("UPDATE users SET money = money + ? WHERE telegram_id=?", (amount, uid))

async def add_xp(uid, xp):
    execute("UPDATE users SET xp = xp + ? WHERE telegram_id=?", (xp, uid))
