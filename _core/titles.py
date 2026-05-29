from db import db

DEFAULT_TITLES = [
    "عضو", "متدرب", "مقاتل", "محارب", "فارس", "بطل", "أسطورة", "خرافي", "لا يقهر",
    "حكيم", "قائد", "ملك", "إمبراطور", "قدوة", "نجم", "سيف", "رمح", "درع", "صقر",
    "أسد", "ذئب", "نمر", "ثعلب", "غزال", "نسر", "باز", "صاعقة", "زلزال", "برق",
    "نور", "ظل", "نار", "ثلج", "ريح", "بحر", "جبل", "وادي", "قمة", "نجمة",
    "كوكب", "قمر", "شمس", "مجد", "عزة", "كرامة", "إخلاص", "وفاء", "صبر", "حكمة"
]

async def init_titles_table():
    await db.execute("""
        CREATE TABLE IF NOT EXISTS titles (
            id SERIAL PRIMARY KEY,
            title TEXT UNIQUE
        )
    """)
    for title in DEFAULT_TITLES:
        await db.execute("INSERT INTO titles (title) VALUES ($1) ON CONFLICT (title) DO NOTHING", title)

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
