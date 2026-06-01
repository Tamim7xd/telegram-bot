import os
import json

def get_backup_info():
    if os.path.exists("backups/backup_current.json"):
        with open("backups/backup_current.json", "r") as f:
            return json.load(f)
    return None