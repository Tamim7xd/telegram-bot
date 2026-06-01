SHOP_TIMEOUT = 5

TITLES = {
    1: {"name": "عضو جديد 🌱", "price": 1000},
    2: {"name": "مقاتل ⚔️", "price": 2500},
    3: {"name": "ملك 👑", "price": 5000},
    4: {"name": "VIP 💎", "price": 10000},
    5: {"name": "أسطوري 🔥", "price": 20000},
}

SHOP_MENU = [
    {"name": f"{data['name']} - {data['price']} 🪙", "id": tid}
    for tid, data in TITLES.items()
]