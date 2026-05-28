import sqlite3

conn = sqlite3.connect("bot.db", check_same_thread=False)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    name TEXT,
    messages INTEGER DEFAULT 0,
    money INTEGER DEFAULT 0,
    xp INTEGER DEFAULT 0,
    level INTEGER DEFAULT 1,
    title TEXT DEFAULT 'مبتدئ',
    muted INTEGER DEFAULT 0,
    banned INTEGER DEFAULT 0,
    vip INTEGER DEFAULT 0,
    last_daily INTEGER DEFAULT 0
)
""")

conn.commit()
