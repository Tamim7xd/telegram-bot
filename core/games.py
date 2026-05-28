import random

def random_game():
    games = [
        "سؤال ذكاء 🧠",
        "لغز ⚡",
        "خمن الرقم 🎲",
        "أسرع إجابة 🏃",
        "كلمة عشوائية ❓"
    ]
    return random.choice(games)


def game_reward():
    return {
        "xp": 100,
        "money": random.randint(50, 200)
    }

