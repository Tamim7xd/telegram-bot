 import logging
import time

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def get_logger(name):
    return logging.getLogger(name)

def log_action(conn, admin_id, admin_name, action, target_id, target_name, reason):
    import time
    conn.execute(
        "INSERT INTO logs (admin_id, admin_name, action, target_id, target_name, reason, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (admin_id, admin_name, action, target_id, target_name, reason, int(time.time()))
    )
    conn.commit()