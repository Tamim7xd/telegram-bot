from aiogram import Bot

bot = None

def set_bot(b: Bot):
    global bot
    bot = b
