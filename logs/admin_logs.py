import time
from shared.database import get_db

def log_admin_action(admin_id, action, target_id, reason=""):
    conn = get_db()
    conn.execute(
        "INSERT INTO logs (admin_id, action, target_id, reason, timestamp) VALUES (?, ?, ?, ?, ?)",
        (admin_id, action, target_id, reason, int(time.time()))
    )
    conn.commit()
    conn.close()

def get_admin_logs(limit=50):
    conn = get_db()
    cursor = conn.execute(
        "SELECT * FROM logs ORDER BY timestamp DESC LIMIT ?", (limit,)
    )
    logs = cursor.fetchall()
    conn.close()
    return logs