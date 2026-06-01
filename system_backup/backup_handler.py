import json
import sqlite3
import time
import os
from config import GROUP_ID

BACKUP_FOLDER = "backups"

async def create_backup(bot):
    try:
        os.makedirs(BACKUP_FOLDER, exist_ok=True)
        
        conn = sqlite3.connect("database.db")
        conn.row_factory = sqlite3.Row
        
        users = [dict(row) for row in conn.execute("SELECT * FROM users")]
        admins = [dict(row) for row in conn.execute("SELECT * FROM admins")]
        titles = [dict(row) for row in conn.execute("SELECT * FROM user_titles")]
        logs = [dict(row) for row in conn.execute("SELECT * FROM logs")]
        
        conn.close()
        
        backup_data = {
            "timestamp": int(time.time()),
            "users": users,
            "admins": admins,
            "user_titles": titles,
            "logs": logs
        }
        
        with open(f"{BACKUP_FOLDER}/backup_current.json", "w", encoding="utf-8") as f:
            json.dump(backup_data, f, ensure_ascii=False, indent=2)
        
        await bot.send_message(GROUP_ID, f"💾 **نسخ احتياطي**\n\n✅ تم حفظ البيانات\n🕛 {time.strftime('%Y-%m-%d %H:%M:%S')}\n👥 مستخدمين: {len(users)}", parse_mode="Markdown")
    except Exception as e:
        print(f"Backup error: {e}")