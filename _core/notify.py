from aiogram import Bot

bot = None


def set_bot(b):
    global bot
    bot = b


def get_bot():
    return bot


async def send_notify(uid, title, body, emoji="🔔"):

    if not bot:
        return

    text = (
        f"{emoji} {title}\n"
        f"━━━━━━━━━━━━━━\n"
        f"{body}\n"
        f"━━━━━━━━━━━━━━"
    )

    try:
        await bot.send_message(uid, text)
    except:
        pass
