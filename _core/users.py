from db import db
from aiogram.types import User
from config import STARTING_MONEY, STARTING_XP, ADMIN_IDS


# =====================
# ADMIN CHECK
# =====================
async def is_admin(user_id: int):
    return user_id in ADMIN_IDS


# =====================
# GET USER (مفقود عندك وكان سبب الخطأ)
# =====================
async def get_user(telegram_id: int):
    return await db.fetchrow(
        "SELECT * FROM users WHERE telegram_id = ?",
        telegram_id
    )


# =====================
# CREATE OR GET USER
# =====================
async def get_or_create_user(tg_user: User):
    user = await get_user(tg_user.id)

    if user:
        return user

    await db.execute(
        "INSERT INTO users (telegram_id, username, full_name, money, xp) VALUES (?, ?, ?, ?, ?)",
        tg_user.id,
        tg_user.username,
        tg_user.full_name,
        STARTING_MONEY,
        STARTING_XP
    )

    return await get_user(tg_user.id)


# =====================
# MONEY SYSTEM
# =====================
async def update_user_money(user_id: int, amount: int, reason="", admin_id=None):
    await db.execute(
        "UPDATE users SET money = money + ? WHERE telegram_id = ?",
        amount,
        user_id
    )


# =====================
# XP SYSTEM
# =====================
async def update_user_xp(user_id: int, amount: int):
    await db.execute(
        "UPDATE users SET xp = xp + ? WHERE telegram_id = ?",
        amount,
        user_id
    )


# =====================
# STATUS
# =====================
async def set_user_status(user_id: int, status: str):
    await db.execute(
        "UPDATE users SET status = ? WHERE telegram_id = ?",
        status,
        user_id
    )


async def get_user_status(user_id: int):
    row = await get_user(user_id)
    return row["status"] if row else "active"


# =====================
# GENERAL MODS (اختياري لكن موجود في مشروعك)
# =====================
async def is_general_mod(user_id: int):
    row = await db.fetchrow(
        "SELECT 1 FROM general_mods WHERE user_id = ?",
        user_id
    )
    return row is not None


async def add_general_mod(user_id: int, added_by: int):
    await db.execute(
        "INSERT OR IGNORE INTO general_mods (user_id, added_by) VALUES (?, ?)",
        user_id,
        added_by
    )


async def remove_general_mod(user_id: int):
    await db.execute(
        "DELETE FROM general_mods WHERE user_id = ?",
        user_id
    )
