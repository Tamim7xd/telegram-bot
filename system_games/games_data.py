GAME_REWARD = 250
GAME_TIMEOUT = 5

# 1️⃣ تخمين الرقم
GUESS_NUMBER_CONFIG = {
    "min": 1,
    "max": 100,
    "reward": 250
}

# 2️⃣ حجر ورقة مقص
RPS_CONFIG = {
    "choices": ["حجر", "ورقة", "مقص"],
    "rules": {
        "حجر": "مقص",
        "ورقة": "حجر",
        "مقص": "ورقة"
    },
    "reward": 250
}

# 3️⃣ الأسئلة العامة
QUESTIONS = [
    {"q": "ما عاصمة مصر؟", "a": "القاهرة"},
    {"q": "ما عاصمة السعودية؟", "a": "الرياض"},
    {"q": "ما لون البحر؟", "a": "أزرق"},
    {"q": "كم عدد أيام الأسبوع؟", "a": "سبعة"},
    {"q": "ما عاصمة فرنسا؟", "a": "باريس"},
]

# 4️⃣ الكلمات المعكوسة
REVERSE_WORDS = [
    {"word": "قطار", "reverse": "راطق"},
    {"word": "مدرسة", "reverse": "ةسردم"},
    {"word": "كتاب", "reverse": "باتك"},
]

# 5️⃣ لعبة الحظ
LUCKY_NUMBER_CONFIG = {
    "min": 1,
    "max": 10,
    "reward": 250
}

# 6️⃣ لوكي بوكس
LUCKY_BOX_CONFIG = {
    "rewards": [
        {"amount": 0, "chance": 70, "message": "😭 للأسف... لم تحصل على شيء"},
        {"amount": 250, "chance": 15, "message": "🎉 حصلت على 250 عملة"},
        {"amount": 500, "chance": 10, "message": "🌟🌟 حصلت على 500 عملة"},
        {"amount": 1000, "chance": 5, "message": "✨✨✨ جاكبوت! حصلت على 1000 عملة"}
    ],
    "cooldown_minutes": 5,
    "max_per_day": 10
}

# قائمة الألعاب
GAMES_MENU = [
    {"name": "تخمين الرقم 🔢", "callback": "guess_number"},
    {"name": "حجر ورقة مقص ✊", "callback": "rps"},
    {"name": "أسئلة عامة ❓", "callback": "questions"},
    {"name": "كلمات معكوسة 🔄", "callback": "reverse_words"},
    {"name": "لعبة الحظ 🎲", "callback": "lucky_number"},
    {"name": "لوكي بوكس 🎁", "callback": "lucky_box"},
]