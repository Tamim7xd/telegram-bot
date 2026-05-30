from db import db

async def get_available_titles():
    rows = await db.fetch("SELECT title FROM titles ORDER BY id")
    return [r['title'] for r in rows]

async def add_custom_title(title: str):
    await db.execute("INSERT INTO titles (title) VALUES (?) ON CONFLICT DO NOTHING", title)

async def set_user_title(telegram_id: int, title: str):
    exists = await db.fetchval("SELECT 1 FROM titles WHERE title = ?", title)
    if not exists:
        return False
    await db.execute("UPDATE users SET title = ? WHERE telegram_id = ?", title, telegram_id)
    return True

async def remove_user_title(telegram_id: int):
    await db.execute("UPDATE users SET title = '' WHERE telegram_id = ?", telegram_id)

def register_titles_handlers(dp):
    pass
