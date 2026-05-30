import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "").split(","))) if os.getenv("ADMIN_IDS") else []
GROUP_ID = int(os.getenv("GROUP_ID", 0)) if os.getenv("GROUP_ID") else None   # ✅ جديد
print(f"✅ GROUP_ID من البيئة: {GROUP_ID}")
XP_PER_MESSAGE = 5
XP_PER_LEVEL = 250
LEVELUP_BONUS_MONEY = 500
LEVELUP_BONUS_XP = 100

CURRENCY_NAME = "دينار"
STARTING_MONEY = 100
STARTING_XP = 0

GAME_TIME_LIMIT = 20
DEFAULT_GAME_PRIZE_MIN = 50
DEFAULT_GAME_PRIZE_MAX = 300
DATA_DIR = "data"

print(f"✅ الأدمن: {ADMIN_IDS}")
print(f"✅ المجموعة المستهدفة للإشعارات: {GROUP_ID}")
