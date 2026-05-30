import sqlite3
from config import ADMIN_IDS

DB_FILE = "bot_data.db"

def get_conn():
    return sqlite3.connect(DB_FILE)

def init_db():
    conn = get_conn()
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        telegram_id INTEGER PRIMARY KEY,
        username TEXT,
        full_name TEXT,
        money INTEGER DEFAULT 100,
        xp INTEGER DEFAULT 0,
        level INTEGER DEFAULT 1,
        title TEXT DEFAULT '',
        status TEXT DEFAULT 'active'
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS admins (
        user_id INTEGER PRIMARY KEY
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS game_sessions (
        chat_id INTEGER,
        message_id INTEGER,
        answer TEXT,
        prize INTEGER,
        status TEXT DEFAULT 'waiting'
    )
    """)

    for aid in ADMIN_IDS:
        c.execute("INSERT OR IGNORE INTO admins (user_id) VALUES (?)", (aid,))

    conn.commit()
    conn.close()

def execute(q, params=()):
    conn = get_conn()
    c = conn.cursor()
    c.execute(q, params)
    conn.commit()
    conn.close()

def fetchone(q, params=()):
    conn = get_conn()
    c = conn.cursor()
    c.execute(q, params)
    row = c.fetchone()
    conn.close()
    return row

def fetchall(q, params=()):
    conn = get_conn()
    c = conn.cursor()
    c.execute(q, params)
    rows = c.fetchall()
    conn.close()
    return rows
