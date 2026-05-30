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
    for f in os.listdir(DATA_DIR):
        if f.endswith(".json"):
            name = f.replace(".json","")
            try:
                with open(os.path.join(DATA_DIR, f), "r", encoding="utf-8") as fp:
                    games_data[name] = json.load(fp)
                print(f"✅ تحميل {len(games_data[name])} سؤال من {f}")
            except:
                games_data[name] = []

async def get_random_game(prize, game_type=None):
    if not games_data:
        load_all_games()
    available = [t for t,items in games_data.items() if items]
    if not available:
        return None
    if game_type and game_type in available:
        chosen = game_type
    else:
        chosen = random.choice(available)
    item = random.choice(games_data[chosen])
    if chosen == "puzzles":
        ans = item["answer"]
        disp = f"🧩 {item['question']}\n⏳ {GAME_TIME_LIMIT} ث\n💰 الجائزة: {prize}"
    elif chosen == "general_qa":
        ans = item["answer"]
        disp = f"❓ {item['question']}\n💰 {prize}"
    elif chosen == "mcq":
        opts = "\n".join([f"{chr(1575+i)}. {opt}" for i,opt in enumerate(item['options'])])
        ans = item['correct']
        disp = f"🔘 {item['question']}\n{opts}\n💰 {prize}\nأرسل الحرف (أ،ب،ج،د)"
    elif chosen == "speed_words":
        ans = item['reversed']
        disp = f"⚡ اكتب معكوس: {item['word']}\n💰 {prize}"
    elif chosen == "proverbs":
        ans = item['complete']
        disp = f"📜 أكمل: {item['partial']}\n💰 {prize}"
    elif chosen == "luck_boxes":
        ans = "box"
        disp = f"🎁 اختر صندوقاً (1-5)\n💰 عشوائي"
    else:
        return None
    return {"type": chosen, "question": item.get('question',''), "answer": str(ans).strip().lower(), "display_text": disp, "prize": prize}

async def save_game_session(chat_id, mid, gtype, q, a, prize):
    await db.execute("INSERT INTO game_sessions (chat_id, message_id, game_type, question, answer, prize_money, status) VALUES (?, ?, ?, ?, ?, ?, 'waiting')", chat_id, mid, gtype, q, a, prize)

async def get_game_session(chat_id, mid):
    return await db.fetchrow("SELECT * FROM game_sessions WHERE chat_id=? AND message_id=?", chat_id, mid)

async def update_game_session_status(chat_id, mid, status):
    await db.execute("UPDATE game_sessions SET status=? WHERE chat_id=? AND message_id=?", status, chat_id, mid)

async def check_answer(chat_id, mid, user_ans):
    s = await get_game_session(chat_id, mid)
    if not s or s['status'] != 'waiting':
        return None
    if s['game_type'] == "luck_boxes":
        try:
            box = int(user_ans.strip())
            if 1<=box<=5:
                prize = random.randint(10,200)
                await update_game_session_status(chat_id, mid, 'finished')
                return prize
        except:
            return 0
    if user_ans.strip().lower() == s['answer']:
        await update_game_session_status(chat_id, mid, 'finished')
        return s['prize_money']
    return 0

load_all_games()
