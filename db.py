import sqlite3

conn = sqlite3.connect(
    "bot.db",
    check_same_thread=False
)

c = conn.cursor()


def init_db():

    c.execute("""
    CREATE TABLE IF NOT EXISTS users(

        user_id INTEGER PRIMARY KEY,
        name TEXT,

        messages INTEGER DEFAULT 0,
        money INTEGER DEFAULT 0,

        xp INTEGER DEFAULT 0,
        level INTEGER DEFAULT 1,

        warns INTEGER DEFAULT 0,
        rewards INTEGER DEFAULT 0,

        title TEXT DEFAULT '🌱 المبتدئ',

        title_locked INTEGER DEFAULT 0,

        banned INTEGER DEFAULT 0,
        muted INTEGER DEFAULT 0
    )
    """)

    conn.commit()
