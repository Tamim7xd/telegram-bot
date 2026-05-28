from telegram import Bot


# =========================
# إشعار مستخدم
# =========================
async def notify_user(bot: Bot, uid: int, text: str):
    try:
        await bot.send_message(chat_id=uid, text=text, parse_mode="HTML")
    except:
        pass


# =========================
# إشعار مجموعة
# =========================
async def notify_group(bot: Bot, gid: int, text: str):
    try:
        await bot.send_message(chat_id=gid, text=text, parse_mode="HTML")
    except:
        pass


# =========================
# ترقية مستوى
# =========================
async def notify_levelup(bot: Bot, uid: int, level: int, title: str):
    await notify_user(bot, uid, f"""
🎉 <b>ترقية جديدة!</b>

⭐ المستوى: {level}
🏆 اللقب: {title}

🔥 استمر في اللعب!
""")


# =========================
# فوز لعبة
# =========================
async def notify_game_win(bot: Bot, uid: int, reward: int):
    await notify_user(bot, uid, f"""
🏆 <b>فزت في اللعبة!</b>

💰 المكافأة: {reward}
🔥 تم إضافتها لحسابك
""")


# =========================
# تعديل إداري
# =========================
async def notify_admin(bot: Bot, text: str, gid: int):
    await notify_group(bot, gid, f"""
🛠 <b>إجراء إداري</b>

{text}
""")
