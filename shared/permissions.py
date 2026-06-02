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

def get_user_role(user_id):
    """تحديد دور العضو (مالك، مشرف إداري، مشرف عادي، لديه لقب، عضو عادي)"""
    if is_owner(user_id):
        return "owner"
    
    if is_super_admin(user_id):
        return "super_admin"
    
    if is_admin(user_id):
        return "admin"
    
    conn = get_db()
    cursor = conn.execute("SELECT title FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    
    if user and user["title"]:
        return "has_title"
    
    return "member"

def get_user_display_name(user_id, first_name):
    """الحصول على الاسم الذي يجب أن يظهر للعضو بناءً على دوره"""
    role = get_user_role(user_id)
    
    if role == "owner":
        return f"المالك {first_name}"
    elif role == "super_admin":
        return f"مشرف إداري {first_name}"
    elif role == "admin":
        return f"مشرف {first_name}"
    elif role == "has_title":
        conn = get_db()
        cursor = conn.execute("SELECT title FROM users WHERE user_id = ?", (user_id,))
        user = cursor.fetchone()
        conn.close()
        return f"{user['title']} {first_name}"
    else:
        return f"عضو {first_name}"
