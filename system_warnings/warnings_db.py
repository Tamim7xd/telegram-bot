from shared.database import get_db

def get_warnings(user_id):
    conn = get_db()
    cursor = conn.execute("SELECT warnings FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result["warnings"] if result else 0

def reset_warnings(user_id):
    conn = get_db()
    conn.execute("UPDATE users SET warnings = 0 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()