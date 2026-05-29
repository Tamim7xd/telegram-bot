async def get_user(user_id: int):
    return {
        "id": user_id,
        "full_name": "User",
        "money": 0,
        "xp": 0,
        "level": 1,
        "title": None
    }

async def update_user_money(user_id, amount, reason, admin_id):
    pass

async def set_user_status(user_id, status):
    pass

async def get_user_role(user_id):
    return "user"
