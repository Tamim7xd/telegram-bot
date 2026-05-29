import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")
ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "").split(","))) if os.getenv("ADMIN_IDS") else []

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

# Data files
DATA_DIR = "data"
