from config import XP_PER_LEVEL
from db import execute, fetchone

async def update_level(uid):
    user = fetchone("SELECT xp, level FROM users WHERE telegram_id=?", (uid,))
    if not user:
        return

    xp, level = user
    new_level = xp // XP_PER_LEVEL + 1

    if new_level > level:
        execute("UPDATE users SET level=? WHERE telegram_id=?", (new_level, uid))
