import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "").split(","))) if os.getenv("ADMIN_IDS") else []
GROUP_ID = int(os.getenv("GROUP_ID", 0)) if os.getenv("GROUP_ID") else None

# XP settings
XP_PER_MESSAGE = 5
XP_PER_LEVEL = 250
LEVELUP_BONUS_MONEY = 500
LEVELUP_BONUS_XP = 100

# Economy
CURRENCY_NAME = "دينار"
STARTING_MONEY = 100
STARTING_XP = 0

# Games
GAME_COOLDOWN = 30
DEFAULT_GAME_PRIZE_MIN = 50
DEFAULT_GAME_PRIZE_MAX = 300
GAME_TIME_LIMIT = 20

# Sounds
SOUNDS_ENABLED = True
SOUNDS_PATH = "sounds/"

# Data files directory
DATA_DIR = "data"

print(f"✅ BOT_TOKEN موجود: {bool(BOT_TOKEN)}")
print(f"✅ ADMIN_IDS: {ADMIN_IDS}")
if GROUP_ID:
    print(f"✅ GROUP_ID: {GROUP_ID}")
