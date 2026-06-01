from shared.database import get_db
from config import OWNER_ID

def is_owner(user_id):
    return user_id == OWNER_ID

def is_admin(user_id):
    conn = get_db()
    cursor = conn.execute("SELECT user_id FROM admins WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result is not None

def is_super_admin(user_id):
    conn = get_db()
    cursor = conn.execute("SELECT user_id FROM admins WHERE user_id = ? AND is_super_admin = 1", (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result is not None

def add_admin(user_id, username, is_super=False):
    conn = get_db()
    conn.execute("INSERT OR REPLACE INTO admins (user_id, username, is_super_admin) VALUES (?, ?, ?)", 
                 (user_id, username, 1 if is_super else 0))
    conn.commit()
    conn.close()

def remove_admin(user_id):
    conn = get_db()
    conn.execute("DELETE FROM admins WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

def get_all_admins():
    conn = get_db()
    cursor = conn.execute("SELECT user_id, username, is_super_admin FROM admins")
    result = cursor.fetchall()
    conn.close()
    return result

def get_admin_info(user_id):
    conn = get_db()
    cursor = conn.execute("SELECT user_id, username, is_super_admin FROM admins WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result