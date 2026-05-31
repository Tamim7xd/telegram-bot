# system_backup/backup_handler.py

import json
import sqlite3
import time
from config import OWNER_ID

async def create_backup(bot):
    try:
        conn = sqlite3.connect("database.db")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM users")
        users = [dict(row) for row in cursor.fetchall()]
        
        cursor.execute("SELECT * FROM admins")
        admins = [dict(row) for row in cursor.fetchall()]
        
        cursor.execute("SELECT * FROM user_titles")
        titles = [dict(row) for row in cursor.fetchall()]
        
        cursor.execute("SELECT * FROM logs")
        logs = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        
        backup_data = {
            "timestamp": int(time.time()),
            "users": users,
            "admins": admins,
            "user_titles": titles,
            "logs": logs
        }
        
        import os
        os.makedirs("backups", exist_ok=True)
        
        with open("backups/backup_current.json", "w", encoding="utf-8") as f:
            json.dump(backup_data, f, ensure_ascii=False, indent=2)
        
        await bot.send_message(
            OWNER_ID,
            f"💾 **نسخ احتياطي تلقائي**\n\n"
            f"✅ تم إنشاء نسخة جديدة\n"
            f"🕛 الوقت: {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"👥 مستخدمين: {len(users)}\n"
            f"🛡️ مشرفين: {len(admins)}\n\n"
            f"📁 الملف: backups/backup_current.json",
            parse_mode="Markdown"
        )
    except Exception as e:
        print(f"Backup error: {e}")