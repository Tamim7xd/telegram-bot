import sqlite3
import time
import os

DB_PATH = "database.db"

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            balance INTEGER DEFAULT 1000,
            warnings INTEGER DEFAULT 0,
            messages INTEGER DEFAULT 0,
            level INTEGER DEFAULT 1,
            title TEXT,
            is_muted INTEGER DEFAULT 0,
            muted_until INTEGER DEFAULT 0,
            is_banned INTEGER DEFAULT 0,
            last_daily TEXT
        )
    ''')
    
    conn.execute('''
        CREATE TABLE IF NOT EXISTS admins (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            is_super_admin INTEGER DEFAULT 0
        )
    ''')
    
    conn.execute('''
        CREATE TABLE IF NOT EXISTS user_titles (
            user_id INTEGER,
            title TEXT,
            purchased_at INTEGER,
            PRIMARY KEY (user_id, title)
        )
    ''')
    
    conn.execute('''
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            admin_id INTEGER,
            admin_name TEXT,
            action TEXT,
            target_id INTEGER,
            target_name TEXT,
            reason TEXT,
            timestamp INTEGER
        )
    ''')
    
    from config import OWNER_ID
    conn.execute("INSERT OR IGNORE INTO admins (user_id, is_super_admin) VALUES (?, 1)", (OWNER_ID,))
    
    conn.commit()
    conn.close()

init_db()

async def update_user_name(context, user_id, first_name):
    """تحديث اسم العضو في المجموعة بناءً على دوره"""
    from config import GROUP_ID
    from shared.permissions import get_user_display_name
    
    new_name = get_user_display_name(user_id, first_name)
    
    try:
        await context.bot.set_chat_member_title(GROUP_ID, user_id, new_name)
        print(f"✅ تم تغيير اسم العضو {user_id} إلى: {new_name}")
        return True
    except Exception as e:
        print(f"❌ فشل تغيير اسم العضو {user_id}: {e}")
        return False
