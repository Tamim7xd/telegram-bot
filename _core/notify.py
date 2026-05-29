from aiogram import Bot

bot: Bot | None = None

def set_bot_instance(instance: Bot):
    global bot
    bot = instance


def get_bot() -> Bot:
    if not bot:
        raise RuntimeError("Bot not initialized")
    return bot
