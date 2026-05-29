import random
from Core_.game_engine import load

active = {}


async def start_game(message, cat):

    data = load(cat)

    if not data:
        return await message.answer("❌ لا يوجد بيانات")

    q = random.choice(data)

    active[message.chat.id] = str(q["a"]).lower()

    await message.answer(
        f"🎮 GAME\n"
        f"━━━━━━━━━━━━━━\n"
        f"❓ {q['q']}\n"
        f"━━━━━━━━━━━━━━"
    )


async def check_answer(message):

    if message.chat.id not in active:
        return

    if not message.text:
        return

    if message.text.lower().strip() == active[message.chat.id]:

        del active[message.chat.id]

        await message.reply(
            "🎉 CORRECT!\n"
            "━━━━━━━━━━━━━━\n"
            "🏆 إجابة صحيحة"
        )

        return True

    return False


# 🎮 UI
def game_menu_ui():

    return (
        "🎮 GAME CENTER\n"
        "━━━━━━━━━━━━━━\n"
        "❓ أسئلة\n"
        "🧩 ألغاز\n"
        "📖 حكم\n"
        "⚡ سرعة\n"
        "🎁 حظ\n"
        "━━━━━━━━━━━━━━"
    )
