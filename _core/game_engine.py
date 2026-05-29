import json, os, random
from db import db
from config import DATA_DIR, GAME_TIME_LIMIT

games_data = {}

def load_all_games():
    global games_data
    games_data = {}
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
        return
    for filename in os.listdir(DATA_DIR):
        if filename.endswith(".json"):
            name = filename.replace(".json", "")
            try:
                with open(os.path.join(DATA_DIR, filename), "r", encoding="utf-8") as f:
                    games_data[name] = json.load(f)
                print(f"✅ Loaded {len(games_data[name])} from {filename}")
            except:
                games_data[name] = []

async def get_random_game(prize: int, game_type: str = None):
    if not games_data:
        load_all_games()
    available = [t for t, items in games_data.items() if items]
    if not available:
        return None
    if game_type and game_type in available:
        chosen = game_type
    else:
        chosen = random.choice(available)
    item = random.choice(games_data[chosen])
    if chosen == "puzzles":
        answer = item["answer"]
        display = f"🧩 *لغز:* {item['question']}\n⏳ {GAME_TIME_LIMIT} ثانية\n💰 الجائزة: {prize} دينار"
    elif chosen == "general_qa":
        answer = item["answer"]
        display = f"❓ *سؤال:* {item['question']}\n💰 الجائزة: {prize} دينار"
    elif chosen == "mcq":
        opts = "\n".join([f"{chr(1575+i)}. {opt}" for i, opt in enumerate(item['options'])])
        answer = item['correct']
        display = f"🔘 *اختر الإجابة:*\n{item['question']}\n\n{opts}\n💰 الجائزة: {prize} دينار\nأرسل الحرف (أ، ب، ج، د)"
    elif chosen == "speed_words":
        answer = item['reversed']
        display = f"⚡ *اكتب معكوس:* {item['word']}\n💰 الجائزة: {prize} دينار"
    elif chosen == "proverbs":
        answer = item['complete']
        display = f"📜 *أكمل المثل:* {item['partial']}\n💰 الجائزة: {prize} دينار"
    elif chosen == "luck_boxes":
        answer = "box"
        display = f"🎁 *اختر صندوقاً (1-5)*\n💰 الجائزة: تصل إلى {prize*2} دينار"
    else:
        return None
    return {
        "type": chosen,
        "question": item.get('question', ''),
        "answer": str(answer).strip().lower(),
        "display_text": display,
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
    if session['game_type'] == "luck_boxes":
        try:
            box = int(user_answer.strip())
            if 1 <= box <= 5:
                prize = random.randint(10, 200)
                await update_game_session_status(chat_id, message_id, 'finished')
                return prize
        except:
            return 0
    if user_answer.strip().lower() == session['answer']:
        await update_game_session_status(chat_id, message_id, 'finished')
        return session['prize_money']
    return 0

load_all_games()
