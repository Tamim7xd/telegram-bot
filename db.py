import sqlite3

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
            permissions TEXT DEFAULT 'mute,unmute,ban,unban,kick,warn,info'
        )''')

        c.execute('''CREATE TABLE IF NOT EXISTS user_stats (
            user_id INTEGER PRIMARY KEY,
            total_messages INTEGER DEFAULT 0,
            total_warns INTEGER DEFAULT 0,
            total_mutes INTEGER DEFAULT 0,
            total_bans INTEGER DEFAULT 0,
            total_kicks INTEGER DEFAULT 0,
            total_deductions INTEGER DEFAULT 0
        )''')

        c.execute('''CREATE TABLE IF NOT EXISTS game_sessions (
            chat_id INTEGER,
            message_id INTEGER,
            game_type TEXT,
            question TEXT,
            answer TEXT,
            prize_money INTEGER,
            status TEXT DEFAULT 'waiting',
            PRIMARY KEY (chat_id, message_id)
        )''')

        conn.commit()
        print("✅ DB Ready")

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
        cols = [d[0] for d in c.description] if c.description else []
        return [dict(zip(cols, r)) for r in rows]

async def fetchrow(query, *args):
    with get_conn() as conn:
        c = conn.cursor()
        c.execute(query, args)
        row = c.fetchone()
        if not row:
            return None
        cols = [d[0] for d in c.description]
        return dict(zip(cols, row))

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
