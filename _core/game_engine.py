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
            except:
                games_data[name] = []

async def get_random_game(prize: int, game_type: str = None):
    if not games_data:
        load_all_games()
    type_map = {
        "puzzles": "puzzles", "general": "general_qa", "mcq": "mcq",
        "speed": "speed_words", "proverb": "proverbs", "luck": "luck_boxes"
    }
    if game_type and game_type in type_map:
        target = type_map[game_type]
        if games_data.get(target) and len(games_data[target]) > 0:
            available = [target]
        else:
            return None
    else:
        available = [t for t, items in games_data.items() if items]
    if not available:
        return None
    chosen = random.choice(available)
    item = random.choice(games_data[chosen])
    # تصميم جذاب
    border = "╭━━━━━━━━━━━━━━━╮\n┃"
    if chosen == "puzzles":
        display = f"{border} 🧠 لغز ┃\n╰━━━━━━━━━━━━━━━╯\n\n🧩 *{item['question']}*\n\n⏳ الوقت: {GAME_TIME_LIMIT} ثانية\n💰 الجائزة: {prize} دينار"
        answer = item['answer']
    elif chosen == "general_qa":
        display = f"{border} ❓ سؤال عام ┃\n╰━━━━━━━━━━━━━━━╯\n\n❓ *{item['question']}*\n\n💰 الجائزة: {prize} دينار"
        answer = item['answer']
    elif chosen == "mcq":
        opts = "\n".join([f"{chr(1575+i)}. {opt}" for i, opt in enumerate(item['options'])])
        display = f"{border} 🔘 اختيار من متعدد ┃\n╰━━━━━━━━━━━━━━━╯\n\n🔘 *{item['question']}*\n\n{opts}\n\n💰 الجائزة: {prize} دينار\n📝 أرسل الحرف (أ، ب، ج، د)"
        answer = item['correct']
    elif chosen == "speed_words":
        display = f"{border} ⚡ سرعة ┃\n╰━━━━━━━━━━━━━━━╯\n\n⚡ *اكتب معكوس:* `{item['word']}`\n\n💰 الجائزة: {prize} دينار"
        answer = item['reversed']
    elif chosen == "proverbs":
        display = f"{border} 📜 مثل شعبي ┃\n╰━━━━━━━━━━━━━━━╯\n\n📜 *أكمل المثل:* {item['partial']}\n\n💰 الجائزة: {prize} دينار"
        answer = item['complete']
    elif chosen == "luck_boxes":
        display = f"{border} 🎲 حظ ┃\n╰━━━━━━━━━━━━━━━╯\n\n🎁 *اختر صندوقاً 1-5*\n📦 1  📦 2  📦 3  📦 4  📦 5\n\n💰 الجائزة: عشوائية"
        answer = "box"
    else:
        return None
    return {
        "type": chosen,
        "question": item.get('question', ''),
        "answer": str(answer).strip().lower(),
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
    if session['game_type'] == "luck_boxes":
        try:
            box = int(user_answer.strip())
            if 1 <= box <= 5:
                prizes = {1: (10,50), 2: (50,100), 3: (100,200), 4: (200,350), 5: (350,500)}
                mn, mx = prizes.get(box, (10,100))
                prize = random.randint(mn, mx)
                await update_game_session_status(chat_id, message_id, 'finished')
                return prize
        except:
            return 0
    correct = user_answer.strip().lower() == session['answer']
    if correct:
        await update_game_session_status(chat_id, message_id, 'finished')
        return session['prize_money']
    return 0

load_all_games()
