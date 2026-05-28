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

        warnings INTEGER DEFAULT 0,

        rewards INTEGER DEFAULT 0,

        custom_title TEXT DEFAULT '',

        title_locked INTEGER DEFAULT 0
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS questions(

        user_id INTEGER PRIMARY KEY,

        answer TEXT
    )
    """)

    conn.commit()
