import random
import asyncio

from db import c, conn
from core.users import add_xp
from core.service import add_message


# =========================
# بنك الأسئلة
# =========================
QUESTIONS = [
    ("ما عاصمة العراق؟", "بغداد"),
    ("2 + 2 = ?", "4"),
    ("ما اسم الكوكب الأحمر؟", "المريخ"),
    ("كم عدد القارات؟", "7"),
    ("ما لغة بايثون؟", "برمجة")
]


# =========================
# حالة اللعبة
# =========================
active_game = {
    "active": False,
    "answer": None,
    "winner": None
}


# =========================
# بدء لعبة
# =========================
async def start_game(bot, chat_id):

    if active_game["active"]:
        return

    q, a = random.choice(QUESTIONS)

    active_game["active"] = True
    active_game["answer"] = a.lower()
    active_game["winner"] = None

    await bot.send_message(chat_id, f"""
🎮 لعبة بدأت!

❓ السؤال:
{q}

⚡ أول إجابة صحيحة تفوز!
""")

    # انتهاء تلقائي بعد 30 ثانية
    await asyncio.sleep(30)

    active_game["active"] = False

    if not active_game["winner"]:
        await bot.send_message(chat_id, "⏱ انتهت اللعبة بدون فائز!")


# =========================
# معالجة الإجابة
# =========================
async def check_answer(bot, message):

    if not active_game["active"]:
        return

    if active_game["winner"]:
        return

    if message.text.lower().strip() == active_game["answer"]:

        user = message.from_user
        active_game["winner"] = user.id

        # مكافآت
        add_xp(user.id, 100)

        c.execute("""
            UPDATE users
            SET money = money + 100
            WHERE user_id=?
        """, (user.id,))
        conn.commit()

        await bot.send_message(
            message.chat.id,
            f"""
🏆 فاز {user.first_name}!

💰 +100 فلوس
🔥 +100 XP
"""
        )

        active_game["active"] = False
