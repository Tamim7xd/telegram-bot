import time

users = {}

def check_spam(uid: int):
    now = time.time()

    if uid not in users:
        users[uid] = []

    users[uid].append(now)

    # آخر 5 رسائل
    users[uid] = users[uid][-5:]

    if len(users[uid]) < 5:
        return False

    if now - users[uid][0] < 4:
        return True

    return False
