
from db import db

async def set_user_title(telegram_id: int, title: str):
    await db.execute("UPDATE users SET title = $1 WHERE telegram_id = $2", title, telegram_id)

async def remove_user_title(telegram_id: int):
    await db.execute("UPDATE users SET title = '' WHERE telegram_id = $1", telegram_id)

def register_titles_handlers(dp):
    pass
