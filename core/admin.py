from db import db
from config import GROUP_ID

conn, c = db()

def is_admin(role):
    return role in ["admin","owner"]

async def notify(bot, text):
    try:
        await bot.send_message(GROUP_ID, f"🔔 {text}")
    except:
        pass
