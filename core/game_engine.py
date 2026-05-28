import random
import asyncio
from db import c, conn
from core.service import add_xp

GAME = {"active": False, "answer": None}

QUESTIONS = [
    ("ما عاصمة العراق؟", "بغداد"),
    ("2+2؟", "4"),
    ("ما لون السماء؟", "أزرق"),
    ("أكبر كوكب؟", "المشتري")
]


async def start_game(bot, chat_id):

    if GAME["active"]:
        return

    q, a = random.choice(QUESTIONS)

    GAME["active"] = True
    GAME["answer"] = a.lower()

    await bot.send_message(chat_id, f"🎮 سؤال:\n\n{q}")

    await asyncio.sleep(20)

    GAME["active"] = False
    await bot.send_message(chat_id, "⏱ انتهت اللعبة")


async def check_answer(bot, message):

    if not GAME["active"]:
        return

    if message.text.lower().strip() == GAME["answer"]:

        GAME["active"] = False

        uid = message.from_user.id

        add_xp(uid, 100)

        c.execute("UPDATE users SET money = money + 100 WHERE user_id=?", (uid,))
        conn.commit()

        await bot.send_message(
            message.chat.id,
            f"🏆 {message.from_user.first_name} فاز! +100"
        )
