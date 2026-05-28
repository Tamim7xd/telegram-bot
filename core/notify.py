from telegram import Bot

# =========================
# إشعار للمستخدم
# =========================
async def notify_user(bot: Bot, user_id: int, text: str):
    try:
        await bot.send_message(user_id, text)
    except:
        pass


# =========================
# إشعار للمجموعة
# =========================
async def notify_group(bot: Bot, group_id: int, text: str):
    try:
        await bot.send_message(group_id, text)
    except:
        pass
