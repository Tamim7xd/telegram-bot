import random


QUESTIONS = [

    {
        "question": "ما عاصمة العراق ؟",
        "answer": "بغداد"
    },

    {
        "question": "ما أكبر كوكب ؟",
        "answer": "المشتري"
    },

    {
        "question": "كم عدد أيام الأسبوع ؟",
        "answer": "7"
    },

    {
        "question": "ما لون السماء ؟",
        "answer": "ازرق"
    },

    {
        "question": "كم عدد القارات ؟",
        "answer": "7"
    },

    {
        "question": "ما عاصمة فرنسا ؟",
        "answer": "باريس"
    },

    {
        "question": "ما أسرع حيوان ؟",
        "answer": "الفهد"
    },

    {
        "question": "ما اسم كوكبنا ؟",
        "answer": "الارض"
    },

    {
        "question": "كم عدد أشهر السنة ؟",
        "answer": "12"
    },

    {
        "question": "ما لون العشب ؟",
        "answer": "اخضر"
    }

] * 10


# =========================
# RANDOM QUESTION
# =========================
def random_question():

    return random.choice(QUESTIONS)
