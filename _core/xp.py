from db import db
from config import XP_PER_LEVEL, LEVELUP_BONUS_MONEY, LEVELUP_BONUS_XP
from _core.users import update_user_money, update_user_xp, get_user

async def get_xp_progress(telegram_id: int):
    user = await get_user(telegram_id)
    xp = user["xp"]
    level = user["level"]
    xp_in_level = xp - (level-1)*XP_PER_LEVEL
    needed = XP_PER_LEVEL
    percent = int((xp_in_level / needed) * 100)
    bar_length = 20
    filled = int(bar_length * xp_in_level / needed)
    bar = "█" * filled + "░" * (bar_length - filled)
    return {
        "current_xp": xp_in_level,
        "needed_xp": needed,
        "percent": percent,
        "bar": bar,
        "level": level,
        "remaining": needed - xp_in_level
    }

async def add_xp(telegram_id: int, amount: int, chat_id: int = None, user_name: str = ""):
    await update_user_xp(telegram_id, amount)
    user = await get_user(telegram_id)
    level = user["level"]
    xp = user["xp"]
    new_level = 1 + (xp // XP_PER_LEVEL)
    if new_level > level:
        await db.execute("UPDATE users SET level = $1 WHERE telegram_id = $2", new_level, telegram_id)
        await update_user_money(telegram_id, LEVELUP_BONUS_MONEY, "مكافأة ترقية مستوى", None)
        await update_user_xp(telegram_id, LEVELUP_BONUS_XP)
        if chat_id:
            from _core.notify import send_levelup_notification
            await send_levelup_notification(chat_id, telegram_id, new_level, user_name)
        return new_level
    return None

def register_xp_handlers(dp):
    pass
