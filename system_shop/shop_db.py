from shared.database import get_db

def get_user_title(user_id):
    conn = get_db()
    cursor = conn.execute("SELECT title FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result["title"] if result else None

def set_user_title(user_id, title):
    conn = get_db()
    conn.execute("UPDATE users SET title = ? WHERE user_id = ?", (title, user_id))
    conn.commit()
    conn.close()