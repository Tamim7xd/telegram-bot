import sqlite3
import os
from config import ADMIN_IDS

DATABASE_FILE = "bot_data.db"

def get_connection():
    return sqlite3.connect(DATABASE_FILE)

async def init_db():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
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
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS admins (
                user_id INTEGER PRIMARY KEY,
                permissions TEXT DEFAULT 'all',
                added_by INTEGER
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS mods (
                user_id INTEGER PRIMARY KEY,
                added_by INTEGER,
                permissions TEXT DEFAULT 'mute,unmute,info,warn',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS temp_bans (
                user_id INTEGER,
                chat_id INTEGER,
                until TIMESTAMP,
                reason TEXT,
                PRIMARY KEY (user_id, chat_id)
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS shop_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE,
                price INTEGER,
                rank_level INTEGER,
                description TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_purchases (
                user_id INTEGER,
                item_id INTEGER,
                purchased_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, item_id)
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_stats (
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
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS guild_settings (
                chat_id INTEGER PRIMARY KEY,
                welcome_message TEXT,
                enable_games INTEGER DEFAULT 1,
                game_cooldown INTEGER DEFAULT 30,
                sound_enabled INTEGER DEFAULT 1,
                levelup_message TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS game_sessions (
                chat_id INTEGER,
                message_id INTEGER,
                game_type TEXT,
                question TEXT,
                answer TEXT,
                prize_money INTEGER,
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'waiting',
                PRIMARY KEY (chat_id, message_id)
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS economy_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                amount INTEGER,
                reason TEXT,
                admin_id INTEGER,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS titles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT UNIQUE
            )
        ''')
        # إضافة الألقاب الافتراضية
        default_titles = [
            "عضو", "متدرب", "مقاتل", "محارب", "فارس", "بطل", "أسطورة", "خرافي", "لا يقهر",
            "حكيم", "قائد", "ملك", "إمبراطور", "قدوة", "نجم", "سيف", "رمح", "درع", "صقر",
            "أسد", "ذئب", "نمر", "ثعلب", "غزال", "نسر", "باز", "صاعقة", "زلزال", "برق",
            "نور", "ظل", "نار", "ثلج", "ريح", "بحر", "جبل", "وادي", "قمة", "نجمة",
            "كوكب", "قمر", "شمس", "مجد", "عزة", "كرامة", "إخلاص", "وفاء", "صبر", "حكمة"
        ]
        for title in default_titles:
            cursor.execute("INSERT OR IGNORE INTO titles (title) VALUES (?)", (title,))
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
            cursor.execute("INSERT OR IGNORE INTO shop_items (name, price, rank_level, description) VALUES (?, ?, ?, ?)", (name, price, level, desc))
        # إضافة الأدمن من الإعدادات
        for admin_id in ADMIN_IDS:
            cursor.execute("INSERT OR IGNORE INTO admins (user_id, permissions, added_by) VALUES (?, 'all', 0)", (admin_id,))
        conn.commit()
        print("✅ تم إنشاء قاعدة بيانات SQLite وجميع الجداول")

# دوال مساعدة غير متزامنة (لكننا سنحولها إلى متزامنة بسيطة)
def execute_query(query, params=()):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        return cursor

def fetch_all(query, params=()):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        return cursor.fetchall()

def fetch_one(query, params=()):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        return cursor.fetchone()

# دوال async متوافقة مع البوت
async def async_execute(query, *args):
    execute_query(query, args)
    return None

async def async_fetch(query, *args):
    rows = fetch_all(query, args)
    # تحويل الصفوف إلى قاموس
    result = []
    for row in rows:
        result.append(dict(zip([desc[0] for desc in cursor.description], row))) if 'cursor' in locals() else result.append(row)
    return result

async def async_fetchrow(query, *args):
    row = fetch_one(query, args)
    if row:
        # نحتاج لأسماء الأعمدة
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, args)
            col_names = [desc[0] for desc in cursor.description]
            return dict(zip(col_names, row))
    return None

async def async_fetchval(query, *args):
    row = fetch_one(query, args)
    return row[0] if row else None

# قاعدة بيانات افتراضية متوافقة مع الكود القديم
class Database:
    async def execute(self, query, *args):
        return await async_execute(query, *args)
    async def fetch(self, query, *args):
        return await async_fetch(query, *args)
    async def fetchrow(self, query, *args):
        return await async_fetchrow(query, *args)
    async def fetchval(self, query, *args):
        return await async_fetchval(query, *args)
    async def connect(self):
        await init_db()
    async def init_tables(self):
        await init_db()
        print("✅ قاعدة البيانات جاهزة")

db = Database()
