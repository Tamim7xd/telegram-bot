from db import db
from aiogram.types import User
from config import STARTING_MONEY, STARTING_XP, ADMIN_IDS


async def is_admin(user_id: int):
    return user_id in ADMIN_IDS


async def get_or_create_user(tg_user: User):
    row = await db.fetchrow(
        "SELECT * FROM users WHERE telegram_id = ?",
        tg_user.id
    )

    if row:
        return row

    await db.execute(
        "INSERT INTO users (telegram_id, username, full_name, money, xp) VALUES (?, ?, ?, ?, ?)",
        tg_user.id,
        tg_user.username,
        tg_user.full_name,
        STARTING_MONEY,
        STARTING_XP
    )

    return await db.fetchrow(
        "SELECT * FROM users WHERE telegram_id = ?",
        tg_user.id
    )


async def update_user_money(uid: int, delta: int, reason="", admin_id=None):
    await db.execute(
        "UPDATE users SET money = money + ? WHERE telegram_id = ?",
        delta,
        uid
    )
