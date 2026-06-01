from shared.database import get_db

def get_user(user_id):
    conn = get_db()
    cursor = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result

def update_user(user_id, **kwargs):
    conn = get_db()
    for key, value in kwargs.items():
        conn.execute(f"UPDATE users SET {key} = ? WHERE user_id = ?", (value, user_id))
    conn.commit()
    conn.close()