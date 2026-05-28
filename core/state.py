states = {}


def set_state(uid, action, target):

    states[uid] = {
        "action": action,
        "target": target
    }


def get_state(uid):
    return states.get(uid)


def clear_state(uid):

    if uid in states:
        del states[uid]
