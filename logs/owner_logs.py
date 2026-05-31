import time
from shared.database import get_db

def log_owner_action(owner_id, action, target_id=None, reason=""):
    conn = get_db()
    conn.execute(
        "INSERT INTO logs (admin_id, action, target_id, reason, timestamp) VALUES (?, ?, ?, ?, ?)",
        (owner_id, f"[مالك] {action}", target_id, reason, int(time.time()))
    )
    conn.commit()
    conn.close()