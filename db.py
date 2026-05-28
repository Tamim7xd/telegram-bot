import sqlite3

conn = sqlite3.connect("bot.db", check_same_thread=False)
c = conn.cursor()

def init_db():
    c.execute("""
    CREATE TABLE IF NOT EXISTS users(
        user_id INTEGER PRIMARY KEY,
        name TEXT,
        xp INTEGER DEFAULT 0,
        messages INTEGER DEFAULT 0,
        role TEXT DEFAULT 'user',
        locked INTEGER DEFAULT 0
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS questions(
        user_id INTEGER PRIMARY KEY,
        answer TEXT
    )
    """)

    conn.commit()

def db():
    return conn, c
