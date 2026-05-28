import sqlite3
import time

conn = sqlite3.connect("bot.db", check_same_thread=False)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS users(
user_id INTEGER PRIMARY KEY,
name TEXT,
money INTEGER DEFAULT 0,
messages INTEGER DEFAULT 0,
title TEXT DEFAULT 'مبتدئ',
start_time INTEGER,
banned INTEGER DEFAULT 0,
muted_until INTEGER DEFAULT 0
)
""")

conn.commit()

def now():
    return int(time.time())