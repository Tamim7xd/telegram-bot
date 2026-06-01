from shared.database import get_db

def get_offenders_count():
    conn = get_db()
    cursor = conn.execute("SELECT COUNT(*) FROM users WHERE is_muted = 1 OR warnings > 0 OR is_banned = 1")
    count = cursor.fetchone()[0]
    conn.close()
    return count