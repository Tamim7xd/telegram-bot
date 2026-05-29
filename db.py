import asyncpg
from config import DATABASE_URL, ADMIN_IDS

class Database:
    def __init__(self):
        self.pool = None

    async def connect(self):
        if not DATABASE_URL:
            raise Exception("DATABASE_URL غير معرف")
        try:
            self.pool = await asyncpg.create_pool(DATABASE_URL)
            print("✅ تم الاتصال بقاعدة البيانات")
        except Exception as e:
            print(f"❌ خطأ في الاتصال: {e}")
            raise

    async def execute(self, query, *args):
        async with self.pool.acquire() as conn:
            return await conn.execute(query, *args)

    async def fetch(self, query, *args):
        async with self.pool.acquire() as conn:
            return await conn.fetch(query, *args)

    async def fetchrow(self, query, *args):
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(query, *args)

    async def fetchval(self, query, *args):
        async with self.pool.acquire() as conn:
            return await conn.fetchval(query, *args)

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
            CREATE TABLE IF NOT EXISTS mods (
                user_id BIGINT PRIMARY KEY,
                added_by BIGINT,
                permissions TEXT DEFAULT 'mute,unmute,info,warn',
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)
        await self.execute("""
            CREATE TABLE IF NOT EXISTS temp_bans (
                user_id BIGINT,
                chat_id BIGINT,
                until TIMESTAMP,
                reason TEXT,
                PRIMARY KEY (user_id, chat_id)
            )
        """)
        await self.execute("""
            CREATE TABLE IF NOT EXISTS shop_items (
                id SERIAL PRIMARY KEY,
                name TEXT UNIQUE,
                price INT,
                rank_level INT,
                description TEXT
            )
        """)
        await self.execute("""
            CREATE TABLE IF NOT EXISTS user_purchases (
                user_id BIGINT,
                item_id INT,
                purchased_at TIMESTAMP DEFAULT NOW(),
                PRIMARY KEY (user_id, item_id)
            )
        """)
        await self.execute("""
            CREATE TABLE IF NOT EXISTS user_stats (
                user_id BIGINT PRIMARY KEY,
                total_messages INT DEFAULT 0,
                total_warns INT DEFAULT 0,
                total_mutes INT DEFAULT 0,
                total_bans INT DEFAULT 0,
                total_kicks INT DEFAULT 0,
                total_deductions INT DEFAULT 0,
                last_deduction_amount INT DEFAULT 0,
                last_deduction_reason TEXT DEFAULT '',
                last_deduction_at TIMESTAMP
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
        await self.execute("""
            CREATE TABLE IF NOT EXISTS titles (
                id SERIAL PRIMARY KEY,
                title TEXT UNIQUE
            )
        """)
        # إضافة الألقاب الافتراضية
        default_titles = [
            "عضو", "متدرب", "مقاتل", "محارب", "فارس", "بطل", "أسطورة", "خرافي", "لا يقهر",
            "حكيم", "قائد", "ملك", "إمبراطور", "قدوة", "نجم", "سيف", "رمح", "درع", "صقر",
            "أسد", "ذئب", "نمر", "ثعلب", "غزال", "نسر", "باز", "صاعقة", "زلزال", "برق",
            "نور", "ظل", "نار", "ثلج", "ريح", "بحر", "جبل", "وادي", "قمة", "نجمة",
            "كوكب", "قمر", "شمس", "مجد", "عزة", "كرامة", "إخلاص", "وفاء", "صبر", "حكمة"
        ]
        for title in default_titles:
            await self.execute("INSERT INTO titles (title) VALUES ($1) ON CONFLICT (title) DO NOTHING", title)
        # إضافة الرتب الافتراضية للمتجر
        default_ranks = [
            ("عضو جديد", 1000, 1, "الرتبة الأساسية"),
            ("متدرب", 2000, 2, "بداية الطريق"),
            ("مقاتل", 3500, 3, "شجاع"),
            ("محارب", 5000, 4, "قوي"),
            ("فارس", 7500, 5, "محترف"),
            ("بطل", 10000, 6, "أسطوري"),
            ("قائد", 15000, 7, "قائد الفريق"),
            ("ملك", 20000, 8, "حاكم"),
            ("إمبراطور", 30000, 9, "عظيم"),
            ("أسطورة", 50000, 10, "خرافي")
        ]
        for name, price, level, desc in default_ranks:
            await self.execute("""
                INSERT INTO shop_items (name, price, rank_level, description)
                VALUES ($1, $2, $3, $4) ON CONFLICT (name) DO NOTHING
            """, name, price, level, desc)
        # إضافة الأدمن من الإعدادات
        for admin_id in ADMIN_IDS:
            await self.execute("INSERT INTO admins (user_id, permissions, added_by) VALUES ($1, 'all', 0) ON CONFLICT (user_id) DO NOTHING", admin_id)
        print("✅ تم إنشاء جميع الجداول")

db = Database()
