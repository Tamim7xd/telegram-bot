STATE = {}

def set_state(admin, action, target):
    STATE[admin] = {"action": action, "target": target}

def get_state(admin):
    return STATE.get(admin)

def clear_state(admin):
    STATE.pop(admin, None)
