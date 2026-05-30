from db import db
from aiogram.types import User
from config import STARTING_MONEY, STARTING_XP, ADMIN_IDS

# ================== الصلاحيات الأساسية ==================
async def is_admin(user_id: int) -> bool:
    """أدمن كامل (من ADMIN_IDS)"""
    return user_id in ADMIN_IDS

async def is_super_admin(user_id: int) -> bool:
    """نفس الأدمن الكامل (للتسمية)"""
    return user_id in ADMIN_IDS

async def is_general_mod(user_id: int) -> bool:
    """مشرف عادي (يُضاف بواسطة الأدمن)"""
    row = await db.fetchrow("SELECT 1 FROM general_mods WHERE user_id = ?", user_id)
    return row is not None

async def is_admin_mod(user_id: int) -> bool:
    """مشرف إداري (صلاحيات إضافية: خصم، مكافئة)"""
    row = await db.fetchrow("SELECT 1 FROM admin_mods WHERE user_id = ?", user_id)
    return row is not None

async def add_general_mod(user_id: int, added_by: int):
    await db.execute("INSERT OR IGNORE INTO general_mods (user_id, added_by, permissions) VALUES (?, ?, 'warn,info,money,show_warns')", user_id, added_by)

async def remove_general_mod(user_id: int):
    await db.execute("DELETE FROM general_mods WHERE user_id = ?", user_id)

async def add_admin_mod(user_id: int, added_by: int):
    await db.execute("INSERT OR IGNORE INTO admin_mods (user_id, added_by, permissions) VALUES (?, ?, 'warn,info,money,show_warns,deduct,give')", user_id, added_by)

async def remove_admin_mod(user_id: int):
    await db.execute("DELETE FROM admin_mods WHERE user_id = ?", user_id)

# ================== نظام التحذيرات ==================
async def add_warning(user_id: int, reason: str, admin_id: int):
    warnings = await get_user_warnings_count(user_id)
    new_count = warnings + 1
    await db.execute("UPDATE users SET warnings = ? WHERE telegram_id = ?", new_count, user_id)
    await db.execute("INSERT INTO warnings_log (user_id, reason, admin_id, created_at) VALUES (?, ?, ?, CURRENT_TIMESTAMP)", user_id, reason, admin_id)
    return new_count

async def get_user_warnings_count(user_id: int) -> int:
    row = await db.fetchrow("SELECT warnings FROM users WHERE telegram_id = ?", user_id)
    return row['warnings'] if row else 0

async def get_user_warnings_list(user_id: int, limit=10):
    rows = await db.fetch("SELECT * FROM warnings_log WHERE user_id = ? ORDER BY created_at DESC LIMIT ?", user_id, limit)
    return rows

async def reset_warnings(user_id: int):
    await db.execute("UPDATE users SET warnings = 0 WHERE telegram_id = ?", user_id)

# ================== دوال المستخدم الأساسية ==================
async def get_or_create_user(tg_user: User):
    row = await db.fetchrow("SELECT * FROM users WHERE telegram_id = $1", tg_user.id)
    if row:
        return dict(row)
    else:
        await db.execute("INSERT INTO users (telegram_id, username, full_name, money, xp) VALUES (?, ?, ?, ?, ?)",
                         tg_user.id, tg_user.username, tg_user.full_name, STARTING_MONEY, STARTING_XP)
        await db.execute("INSERT INTO user_stats (user_id) VALUES (?) ON CONFLICT DO NOTHING", tg_user.id)
        return dict(await db.fetchrow("SELECT * FROM users WHERE telegram_id = $1", tg_user.id))

async def update_user_money(telegram_id: int, delta: int, reason: str = "", admin_id: int = None):
    await db.execute("UPDATE users SET money = money + ? WHERE telegram_id = ?", delta, telegram_id)
    if admin_id:
        await db.execute("INSERT INTO economy_log (user_id, amount, reason, admin_id) VALUES (?, ?, ?, ?)",
                         telegram_id, delta, reason, admin_id)
    return True

async def update_user_xp(telegram_id: int, delta: int):
    await db.execute("UPDATE users SET xp = xp + ? WHERE telegram_id = ?", delta, telegram_id)

async def get_user(telegram_id: int):
    row = await db.fetchrow("SELECT * FROM users WHERE telegram_id = $1", telegram_id)
    return dict(row) if row else None

async def set_user_status(telegram_id: int, status: str):
    await db.execute("UPDATE users SET status = ? WHERE telegram_id = ?", status, telegram_id)

async def get_user_status(telegram_id: int):
    row = await db.fetchrow("SELECT status FROM users WHERE telegram_id = $1", telegram_id)
    return row["status"] if row else "active"

def register_user_handlers(dp):
    pass
