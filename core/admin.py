from config import ADMIN_ID 
from db import db

conn, c = db()

def get_role(uid):
    c.execute("SELECT role FROM users WHERE user_id=?", (uid,))
    r = c.fetchone()
    return r[0] if r else "user"

def is_owner(uid):
    return uid == ADMIN_ID 

def is_admin(uid):
    return get_role(uid) in ["admin","ADMIN"]

def set_role(uid, role):
    c.execute("UPDATE users SET role=? WHERE user_id=?", (role, uid))
    conn.commit()

async def notify(bot, text):
    from config import GROUP_ID
    try:
        await bot.send_message(GROUP_ID, f"🔔 {text}")
    except:
        pass
