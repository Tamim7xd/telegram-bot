import logging
import time
from shared.database import get_db

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/system.log'),
        logging.StreamHandler()
    ]
)

def get_logger(name):
    return logging.getLogger(name)

def log_action(conn, admin_id, admin_name, action, target_id, target_name, reason):
    """تسجيل العملية في قاعدة البيانات"""
    conn.execute(
        "INSERT INTO logs (admin_id, admin_name, action, target_id, target_name, reason, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (admin_id, admin_name, action, target_id, target_name, reason, int(time.time()))
    )
    conn.commit()

def log_error(error_message):
    """تسجيل الأخطاء في ملف السجل"""
    logger = get_logger(__name__)
    logger.error(error_message)

def log_info(info_message):
    """تسجيل معلومات عامة"""
    logger = get_logger(__name__)
    logger.info(info_message)