import json, os, random
from db import db
from config import DATA_DIR, GAME_TIME_LIMIT

games_data = {}

def load_all_games():
    global games_data
    games_data = {}
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
    for filename in os.listdir(DATA_DIR):
        if filename.endswith(".json"):
            name = filename.replace(".json", "")
            with open(os.path.join(DATA_DIR, filename), "r", encoding="utf-8") as f:
                games_data[name] = json.load(f)

async def get_random_game(prize):
    if not games_data:
        load_all_games()
    types = list(games_data.keys())
    if not types:
        return None
    game_type = random.choice(types)
    item = random.choice(games_data[game_type])
    if game_type == "puzzles":
        question = item["question"]
        answer = item["answer"]
        display = f"🧩 *لغز:* {question}\n⏳ لديك {GAME_TIME_LIMIT} ثانية.\n💰 الجائزة: {prize} دينار"
    elif game_type == "general_qa":
        question = item["question"]
        answer = item["answer"]
        display = f"❓ *سؤال:* {question}\n💰 الجائزة: {prize} دينار"
    elif game_type == "mcq":
        question = item["question"]
        options = item["options"]
        answer = item["correct"]
        opts = "\n".join([f"{chr(1575+i)}. {opt}" for i, opt in enumerate(options)])
        display = f"🔘 *اختر الإجابة:*\n{question}\n\n{opts}\n💰 الجائزة: {prize} دينار\nأرسل الحرف (أ، ب، ج، د)"
    elif game_type == "speed_words":
        word = item["word"]
        answer = item["reversed"]
        display = f"⚡ *اكتب معكوس:* {word}\n💰 الجائزة: {prize} دينار"
    elif game_type == "proverbs":
        partial = item["partial"]
        answer = item["complete"]
        display = f"📜 *أكمل المثل:* {partial}\n💰 الجائزة: {prize} دينار"
    elif game_type == "luck_boxes":
        answer = "box"
        display = f"🎁 *صندوق الحظ:* اختر صندوقاً 1-5\n💰 الجائزة: عشوائية"
    else:
        return None
    return {
        "type": game_type,
        "question": question,
        "answer": answer,
        "display_text": display,
        "item": item,
        "prize": prize
    }

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

async def check_answer(chat_id, message_id, user_answer):
    session = await get_game_session(chat_id, message_id)
    if not session or session['status'] != 'waiting':
        return None
    correct = str(user_answer).strip().lower() == str(session['answer']).strip().lower()
    if correct:
        await update_game_session_status(chat_id, message_id, 'finished')
        return session['prize_money']
    return 0

load_all_games()
