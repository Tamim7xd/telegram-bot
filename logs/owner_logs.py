from shared.database import get_db

def log_owner_action(conn, owner_id, owner_name, action, target_id, target_name, reason):
    import time
    conn.execute(
        "INSERT INTO logs (admin_id, admin_name, action, target_id, target_name, reason, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (owner_id, owner_name, f"[مالك] {action}", target_id, target_name, reason, int(time.time()))
    )