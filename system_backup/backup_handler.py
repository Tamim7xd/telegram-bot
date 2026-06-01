import json
import sqlite3
import time
import os
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
        
        os.makedirs("backups", exist_ok=True)
        
        with open("backups/backup_current.json", "w", encoding="utf-8") as f:
            json.dump(backup_data, f, ensure_ascii=False, indent=2)
        
        await bot.send_message(
            OWNER_ID,
            f"💾 **نسخ احتياطي**\n\n"
            f"✅ تم إنشاء نسخة جديدة\n"
            f"🕛 {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"👥 مستخدمين: {len(users)}\n\n"
            f"📁 backups/backup_current.json",
            parse_mode="Markdown"
        )
    except Exception as e:
        print(f"Backup error: {e}")

async def restore_backup(bot):
    try:
        with open("backups/backup_current.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        
        conn = sqlite3.connect("database.db")
        
        # مسح الجداول
        conn.execute("DELETE FROM users")
        conn.execute("DELETE FROM admins")
        conn.execute("DELETE FROM user_titles")
        conn.execute("DELETE FROM logs")
        
        # استعادة البيانات
        for user in data.get("users", []):
            conn.execute("INSERT OR REPLACE INTO users VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", 
                         (user.get("user_id"), user.get("username"), user.get("first_name"),
                          user.get("balance", 1000), user.get("warnings", 0), user.get("messages", 0),
                          user.get("level", 1), user.get("title"), user.get("is_muted", 0),
                          user.get("muted_until", 0), user.get("is_banned", 0), user.get("last_daily")))
        
        for admin in data.get("admins", []):
            conn.execute("INSERT OR REPLACE INTO admins VALUES (?, ?, ?)", 
                         (admin.get("user_id"), admin.get("username"), admin.get("is_super_admin", 0)))
        
        for title in data.get("user_titles", []):
            conn.execute("INSERT OR REPLACE INTO user_titles VALUES (?, ?, ?)", 
                         (title.get("user_id"), title.get("title"), title.get("purchased_at")))
        
        for log in data.get("logs", []):
            conn.execute("INSERT OR REPLACE INTO logs VALUES (?, ?, ?, ?, ?, ?, ?, ?)", 
                         (log.get("id"), log.get("admin_id"), log.get("admin_name"),
                          log.get("action"), log.get("target_id"), log.get("target_name"),
                          log.get("reason"), log.get("timestamp")))
        
        conn.commit()
        conn.close()
        
        await bot.send_message(OWNER_ID, "✅ **تم استعادة النسخة الاحتياطية بنجاح**", parse_mode="Markdown")
    except Exception as e:
        await bot.send_message(OWNER_ID, f"❌ فشل الاستعادة: {e}")