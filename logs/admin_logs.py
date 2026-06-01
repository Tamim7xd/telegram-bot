from shared.database import get_db

def log_admin_action(conn, admin_id, admin_name, action, target_id, target_name, reason):
    import time
    conn.execute(
        "INSERT INTO logs (admin_id, admin_name, action, target_id, target_name, reason, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (admin_id, admin_name, action, target_id, target_name, reason, int(time.time()))
    )