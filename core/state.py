STATE = {}

def set_state(admin_id, action, target):
    STATE[admin_id] = {"action": action, "target": target}

def get_state(admin_id):
    return STATE.get(admin_id)

def clear_state(admin_id):
    if admin_id in STATE:
        del STATE[admin_id]
