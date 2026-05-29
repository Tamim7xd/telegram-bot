users = {}


async def get_user(uid):

    if uid not in users:
        users[uid] = {
            "id": uid,
            "name": f"User {uid}",
            "money": 0,
            "xp": 0,
            "level": 1,
            "title": "مبتدئ",
            "games": 0,
            "wins": 0,
            "losses": 0,
            "status": "active"
        }

    return users[uid]


def update_stats(uid, win=False):

    u = users[uid]

    u["games"] += 1

    if win:
        u["wins"] += 1
    else:
        u["losses"] += 1


def add_money(uid, amount):
    users[uid]["money"] += amount
