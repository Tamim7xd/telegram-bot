import random
from Core_.game_engine import load

active = {}


async def start_game(message, cat):

    data = load(cat)

    if not data:
        return await message.answer("❌ لا يوجد بيانات")

    q = random.choice(data)

    active[message.chat.id] = {
        "answer": str(q["a"]).lower(),
        "question": q["q"]
    }

    await message.answer(
        f"🎮 QUESTION\n"
        f"━━━━━━━━━━━━━━\n"
        f"❓ {q['q']}\n"
        f"━━━━━━━━━━━━━━"
    )


async def check_answer(message):

    if message.chat.id not in active:
        return

    if not message.text:
        return

    game = active[message.chat.id]

    user_answer = message.text.lower().strip()

    if user_answer == game["answer"]:

        del active[message.chat.id]

        await message.reply(
            "🎉 CORRECT!\n"
            "━━━━━━━━━━━━━━\n"
            "🏆 إجابة صحيحة"
        )

        return True

    else:

        await message.reply("❌ خطأ حاول مرة أخرى")
        return False
