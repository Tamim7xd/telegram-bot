from shared.database import get_db

def get_owner_settings():
    conn = get_db()
    cursor = conn.execute("SELECT * FROM settings WHERE key = 'owner'")
    result = cursor.fetchone()
    conn.close()
    return result