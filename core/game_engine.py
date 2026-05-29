import json
import os
import random
from config import DATA_DIR

games_data = {
    "puzzles": [],
    "general_qa": [],
    "mcq": [],
    "speed_words": [],
    "proverbs": [],
    "luck_boxes": []
}

def load_all_games():
    for name in games_data.keys():
        path = os.path.join(DATA_DIR, f"{name}.json")
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                games_data[name] = json.load(f)

async def get_random_game():
    if not any(games_data.values()):
        load_all_games()
    # اختيار نوع عشوائي من الأنواع المتوفرة
    available = [k for k, v in games_data.items() if v]
    if not available:
        return {"type": "error", "display_text": "⚠️ لا توجد ألعاب حالياً، راجع الأدمن.", "question": "", "answer": ""}
    game_type = random.choice(available)
    item = random.choice(games_data[game_type])
    if game_type == "puzzles":
        question = item["question"]
        answer = item["answer"]
        display = f"🧩 *لغز:* {question}\n⏳ لديك {GAME_TIME_LIMIT} ثانية للإجابة.\n💰 الجائزة: {prize}"
    elif game_type == "general_qa":
        question = item["question"]
        answer = item["answer"]
        display = f"❓ *سؤال ثقافي:* {question}"
    elif game_type == "mcq":
        question = item["question"]
        options = item["options"]
        correct = item["correct"]
        answer = correct  # سنقارن بالحرف أو النص
        opts_text = "\n".join([f"{chr(1575+i)}. {opt}" for i, opt in enumerate(options)])
        display = f"🔘 *اختر الإجابة الصحيحة:*\n{question}\n\n{opts_text}\nأرسل الحرف (أ، ب، ج، د)"
    elif game_type == "speed_words":
        word = item["word"]
        reversed_word = item["reversed"]
        question = f"اكتب معكوس كلمة: {word}"
        answer = reversed_word
        display = f"⚡ *لعبة السرعة:* {question}"
    elif game_type == "proverbs":
        partial = item["partial"]
        complete = item["complete"]
        question = f"أكمل المثل: {partial}"
        answer = complete
        display = f"📜 *أكمل المثل:* {question}"
    else:
        question = "صندوق حظ"
        answer = "box"
        display = f"🎁 *صندوق الحظ:* اختر صندوقاً 1-5\nأرسل رقم الصندوق"
    return {
        "type": game_type,
        "question": question,
        "answer": answer,
        "display_text": display,
        "item": item
    }

async def check_answer(chat_id, message_id, user_answer):
    session = await get_game_session(chat_id, message_id)
    if not session or session['status'] != 'waiting':
        return False, None
    # مقارنة مبسطة (تجاهل المسافات والأحرف الكبيرة)
    if str(user_answer).strip().lower() == str(session['answer']).strip().lower():
        await update_game_session_status(chat_id, message_id, 'finished')
        return True, session['prize_money']
    return False, None

async def save_game_session(chat_id, message_id, game_type, question, answer, prize):
    await db.execute("""
        INSERT INTO game_sessions (chat_id, message_id, game_type, question, answer, prize_money, status)
        VALUES ($1, $2, $3, $4, $5, $6, 'waiting')
    """, chat_id, message_id, game_type, question, answer, prize)

async def get_game_session(chat_id, message_id):
    row = await db.fetchrow("SELECT * FROM game_sessions WHERE chat_id=$1 AND message_id=$2", chat_id, message_id)
    return dict(row) if row else None

async def update_game_session_status(chat_id, message_id, status):
    await db.execute("UPDATE game_sessions SET status=$1 WHERE chat_id=$2 AND message_id=$3", status, chat_id, message_id)

# تحميل البيانات فوراً
load_all_games()
