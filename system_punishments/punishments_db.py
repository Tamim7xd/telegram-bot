from shared.database import get_db
import time

def is_muted(user_id):
    conn = get_db()
    cursor = conn.execute("SELECT is_muted, muted_until FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    
    if result and result["is_muted"]:
        if result["muted_until"] > int(time.time()):
            return True
    return False

def is_banned(user_id):
    conn = get_db()
    cursor = conn.execute("SELECT is_banned FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result["is_banned"] == 1 if result else False