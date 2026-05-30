import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

ADMIN_IDS = []
raw_admins = os.getenv("ADMIN_IDS", "")
if raw_admins:
    ADMIN_IDS = [int(x) for x in raw_admins.split(",") if x.strip().isdigit()]

XP_PER_MESSAGE = 5
XP_PER_LEVEL = 250

LEVELUP_BONUS_MONEY = 500
LEVELUP_BONUS_XP = 100

CURRENCY_NAME = "دينار"
STARTING_MONEY = 100
STARTING_XP = 0

GAME_TIME_LIMIT = 20

DATA_DIR = "data"
