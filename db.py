import sqlite3
from config import ADMIN_IDS

DB_FILE = "bot_data.db"

def get_conn():
    return sqlite3.connect(DB_FILE)

def init_db():
    with get_conn() as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS users (
            telegram_id INTEGER PRIMARY KEY,
            username TEXT,
            full_name TEXT,
            messages_count INTEGER DEFAULT 0,
            money INTEGER DEFAULT 100,
            xp INTEGER DEFAULT 0,
            level INTEGER DEFAULT 1,
            title TEXT DEFAULT '',
            warnings INTEGER DEFAULT 0,
            status TEXT DEFAULT 'active',
            game_points INTEGER DEFAULT 0,
            wins INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS general_mods (
            user_id INTEGER PRIMARY KEY,
            added_by INTEGER,
            permissions TEXT DEFAULT 'mute,unmute,ban,unban,kick,warn,info',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS temp_bans (
            user_id INTEGER,
            chat_id INTEGER,
            until TIMESTAMP,
            reason TEXT,
            PRIMARY KEY (user_id, chat_id)
        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS shop_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            price INTEGER,
            rank_level INTEGER,
            description TEXT
        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS user_purchases (
            user_id INTEGER,
            item_id INTEGER,
            purchased_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (user_id, item_id)
        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS user_stats (
            user_id INTEGER PRIMARY KEY,
            total_messages INTEGER DEFAULT 0,
            total_warns INTEGER DEFAULT 0,
            total_mutes INTEGER DEFAULT 0,
            total_bans INTEGER DEFAULT 0,
            total_kicks INTEGER DEFAULT 0,
            total_deductions INTEGER DEFAULT 0,
            last_deduction_amount INTEGER DEFAULT 0,
            last_deduction_reason TEXT DEFAULT '',
            last_deduction_at TIMESTAMP
        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS guild_settings (
            chat_id INTEGER PRIMARY KEY,
            welcome_message TEXT,
            enable_games INTEGER DEFAULT 1,
            game_cooldown INTEGER DEFAULT 30,
            sound_enabled INTEGER DEFAULT 1,
            levelup_message TEXT
        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS game_sessions (
            chat_id INTEGER,
            message_id INTEGER,
            game_type TEXT,
            question TEXT,
            answer TEXT,
            prize_money INTEGER,
            started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'waiting',
            PRIMARY KEY (chat_id, message_id)
        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS economy_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            amount INTEGER,
            reason TEXT,
            admin_id INTEGER,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS titles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT UNIQUE
        )''')
        default_titles = ["عضو", "متدرب", "مقاتل", "محارب", "فارس", "بطل", "أسطورة"]
        for t in default_titles:
            c.execute("INSERT OR IGNORE INTO titles (title) VALUES (?)", (t,))
        ranks = [("عضو جديد", 1000, 1), ("متدرب", 2000, 2), ("مقاتل", 3500, 3),
                 ("محارب", 5000, 4), ("فارس", 7500, 5), ("بطل", 10000, 6),
                 ("قائد", 15000, 7), ("ملك", 20000, 8), ("إمبراطور", 30000, 9),
                 ("أسطورة", 50000, 10)]
        for name, price, level in ranks:
            c.execute("INSERT OR IGNORE INTO shop_items (name, price, rank_level, description) VALUES (?, ?, ?, ?)", (name, price, level, "رتبة"))
        conn.commit()
        print("✅ قاعدة بيانات SQLite جاهزة")

async def execute(query, *args):
    with get_conn() as conn:
        c = conn.cursor()
        c.execute(query, args)
        conn.commit()

async def fetch(query, *args):
    with get_conn() as conn:
        c = conn.cursor()
        c.execute(query, args)
        rows = c.fetchall()
        col = [d[0] for d in c.description]
        return [dict(zip(col, r)) for r in rows]

async def fetchrow(query, *args):
    with get_conn() as conn:
        c = conn.cursor()
        c.execute(query, args)
        row = c.fetchone()
        if row:
            col = [d[0] for d in c.description]
            return dict(zip(col, row))
        return None

async def fetchval(query, *args):
    with get_conn() as conn:
        c = conn.cursor()
        c.execute(query, args)
        r = c.fetchone()
        return r[0] if r else None

class Database:
    async def connect(self):
        init_db()
    async def init_tables(self):
        init_db()
    async def execute(self, q, *a):
        return await execute(q, *a)
    async def fetch(self, q, *a):
        return await fetch(q, *a)
    async def fetchrow(self, q, *a):
        return await fetchrow(q, *a)
    async def fetchval(self, q, *a):
        return await fetchval(q, *a)

db = Database()
