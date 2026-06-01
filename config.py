import os

# متغيرات البيئة (تُقرأ من Railway أو المشغل)
BOT_TOKEN = os.getenv("BOT_TOKEN")
GROUP_ID = int(os.getenv("GROUP_ID", 0))
OWNER_ID = int(os.getenv("OWNER_ID", 0))

# إعدادات عامة
MAX_WARNINGS = 5
DEFAULT_BALANCE = 1000
MESSAGE_TO_LEVEL = 100
LEVEL_REWARD = 1000
GAME_REWARD = 250
DAILY_REWARD = 100           # ✅ أضف هذا السطر
MESSAGE_TIMEOUT = 5

# الإعدادات الأخرى
CURRENCY_ICON = "🪙"
DEFAULT_TITLE = None