from db import db

async def get_available_titles():
    rows = await db.fetch("SELECT title FROM titles ORDER BY id")
    return [r['title'] for r in rows]

async def add_custom_title(title: str):
    await db.execute("INSERT INTO titles (title) VALUES ($1) ON CONFLICT (title) DO NOTHING", title)

async def set_user_title(telegram_id: int, title: str):
    title_exists = await db.fetchval("SELECT 1 FROM titles WHERE title = $1", title)
    if not title_exists:
        return False
    await db.execute("UPDATE users SET title = $1 WHERE telegram_id = $2", title, telegram_id)
    return True

async def remove_user_title(telegram_id: int):
    await db.execute("UPDATE users SET title = '' WHERE telegram_id = $1", telegram_id)

def register_titles_handlers(dp):
    pass
