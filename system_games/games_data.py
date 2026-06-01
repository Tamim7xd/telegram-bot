GAME_REWARD = 250

QUESTIONS = [
    {"q": "ما عاصمة مصر؟", "a": "القاهرة"},
    {"q": "ما عاصمة السعودية؟", "a": "الرياض"},
    {"q": "ما لون البحر؟", "a": "أزرق"},
    {"q": "كم عدد أيام الأسبوع؟", "a": "سبعة"},
    {"q": "ما عاصمة فرنسا؟", "a": "باريس"},
    {"q": "ما أكبر محيط في العالم؟", "a": "الهادئ"},
]

REVERSE_WORDS = [
    {"word": "قطار", "reverse": "راطق"},
    {"word": "مدرسة", "reverse": "ةسردم"},
    {"word": "كتاب", "reverse": "باتك"},
    {"word": "حاسوب", "reverse": "بوساح"},
]

LUCKY_BOX_REWARDS = [
    {"amount": 0, "chance": 70, "message": "😭 للأسف... لم تحصل على شيء"},
    {"amount": 250, "chance": 15, "message": "🎉 حصلت على 250 عملة"},
    {"amount": 500, "chance": 10, "message": "🌟🌟 حصلت على 500 عملة"},
    {"amount": 1000, "chance": 5, "message": "✨✨✨ جاكبوت! حصلت على 1000 عملة"},
]

GAMES_MENU = [
    {"name": "تخمين الرقم 🔢", "callback": "guess"},
    {"name": "حجر ورقة مقص ✊", "callback": "rps"},
    {"name": "أسئلة عامة ❓", "callback": "questions"},
    {"name": "كلمات معكوسة 🔄", "callback": "reverse"},
    {"name": "لعبة الحظ 🎲", "callback": "lucky"},
    {"name": "لوكي بوكس 🎁", "callback": "box"},
]