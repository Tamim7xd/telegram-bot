import asyncpg
from config import DATABASE_URL

class Database:
    def __init__(self):
        self.pool = None

    async def connect(self):
        self.pool = await asyncpg.create_pool(DATABASE_URL)

    async def execute(self, query, *args):
        async with self.pool.acquire() as conn:
            return await conn.execute(query, *args)

    async def fetch(self, query, *args):
        async with self.pool.acquire() as conn:
            return await conn.fetch(query, *args)

    async def fetchrow(self, query, *args):
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(query, *args)

    async def init_tables(self):
        await self.execute("""
            CREATE TABLE IF NOT EXISTS users (
                telegram_id BIGINT PRIMARY KEY,
                username TEXT,
                full_name TEXT,
                messages_count INT DEFAULT 0,
                money INT DEFAULT 100,
                xp INT DEFAULT 0,
                level INT DEFAULT 1,
                title TEXT DEFAULT '',
                warnings INT DEFAULT 0,
                status TEXT DEFAULT 'active',
                game_points INT DEFAULT 0,
                wins INT DEFAULT 0,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)
        await self.execute("""
            CREATE TABLE IF NOT EXISTS admins (
                user_id BIGINT PRIMARY KEY,
                permissions TEXT DEFAULT 'all',
                added_by BIGINT
            )
        """)
        await self.execute("""
            CREATE TABLE IF NOT EXISTS guild_settings (
                chat_id BIGINT PRIMARY KEY,
                welcome_message TEXT,
                enable_games INT DEFAULT 1,
                game_cooldown INT DEFAULT 30,
                sound_enabled INT DEFAULT 1,
                levelup_message TEXT
            )
        """)
        await self.execute("""
            CREATE TABLE IF NOT EXISTS game_sessions (
                chat_id BIGINT,
                message_id INT,
                game_type TEXT,
                question TEXT,
                answer TEXT,
                prize_money INT,
                started_at TIMESTAMP DEFAULT NOW(),
                status TEXT DEFAULT 'waiting',
                PRIMARY KEY (chat_id, message_id)
            )
        """)
        await self.execute("""
            CREATE TABLE IF NOT EXISTS economy_log (
                id SERIAL PRIMARY KEY,
                user_id BIGINT,
                amount INT,
                reason TEXT,
                admin_id BIGINT,
                timestamp TIMESTAMP DEFAULT NOW()
            )
        """)
        # Insert default admin if any
        for admin_id in ADMIN_IDS:
            await self.execute("""
                INSERT INTO admins (user_id, permissions, added_by) VALUES ($1, 'all', 0)
                ON CONFLICT (user_id) DO NOTHING
            """, admin_id)

db = Database()
