import os

BOT_TOKEN = os.getenv("BOT_TOKEN")

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///bot.db")

CURRENCY_NAME = "Coin"
XP_PER_MESSAGE = 5

ADMIN_IDS = []
MOD_IDS = []
OWNER_IDS = []
