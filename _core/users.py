from db import db
from aiogram.types import User
from config import STARTING_MONEY, STARTING_XP

async def get_or_create_user(tg_user: User):
    row = await db.fetchrow("SELECT * FROM users WHERE telegram_id = $1", tg_user.id)
    if row:
        return dict(row)
    else:
        await db.execute(
            "INSERT INTO users (telegram_id, username, full_name, money, xp) VALUES ($1, $2, $3, $4, $5)",
            tg_user.id, tg_user.username, tg_user.full_name, STARTING_MONEY, STARTING_XP
        )
        return dict(await db.fetchrow("SELECT * FROM users WHERE telegram_id = $1", tg_user.id))

async def update_user_money(telegram_id: int, delta: int, reason: str = "", admin_id: int = None):
    await db.execute("UPDATE users SET money = money + $1 WHERE telegram_id = $2", delta, telegram_id)
    if admin_id:
        await db.execute("INSERT INTO economy_log (user_id, amount, reason, admin_id) VALUES ($1, $2, $3, $4)",
                         telegram_id, delta, reason, admin_id)
    return True

async def update_user_xp(telegram_id: int, delta: int):
    await db.execute("UPDATE users SET xp = xp + $1 WHERE telegram_id = $2", delta, telegram_id)

async def get_user(telegram_id: int):
    return await db.fetchrow("SELECT * FROM users WHERE telegram_id = $1", telegram_id)

# ✅ الدوال الجديدة (في نهاية الملف، خارج أي دالة أخرى)
async def set_user_status(telegram_id: int, status: str):
    await db.execute("UPDATE users SET status = $1 WHERE telegram_id = $2", status, telegram_id)

async def get_user_status(telegram_id: int):
    row = await db.fetchrow("SELECT status FROM users WHERE telegram_id = $1", telegram_id)
    return row["status"] if row else "active"

def register_user_handlers(dp):
    pass
