import json
import os
import random
from db import db
from config import DATA_DIR, GAME_TIME_LIMIT

# قاموس يحمل كل الألعاب من ملفات JSON
games_data = {}

def load_all_games():
    """تحميل جميع ملفات JSON من مجلد data"""
    global games_data
    games_data = {}
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
        return
    for filename in os.listdir(DATA_DIR):
        if filename.endswith(".json"):
            name = filename.replace(".json", "")
            file_path = os.path.join(DATA_DIR, filename)
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    games_data[name] = json.load(f)
                print(f"✅ تم تحميل {len(games_data[name])} سؤالاً من {filename}")
            except Exception as e:
                print(f"❌ خطأ في تحميل {filename}: {e}")
                games_data[name] = []

async def get_random_game(prize: int):
    """
    اختيار لعبة عشوائية من أي ملف JSON متوفر
    تعيد قاموساً يحتوي على نوع اللعبة، السؤال، الإجابة، النص المعروض، والجائزة
    """
    if not games_data:
        load_all_games()
    # تصفية الأنواع التي تحتوي على بيانات
    available_types = [t for t, items in games_data.items() if items]
    if not available_types:
        return None
    game_type = random.choice(available_types)
    item = random.choice(games_data[game_type])
    
    # بناء النص حسب نوع اللعبة
    if game_type == "puzzles":
        question = item["question"]
        answer = item["answer"]
        display = f"🧩 *لغز:* {question}\n⏳ لديك {GAME_TIME_LIMIT} ثانية للإجابة.\n💰 الجائزة: {prize} دينار"
    
    elif game_type == "general_qa":
        question = item["question"]
        answer = item["answer"]
        display = f"❓ *سؤال ثقافي:* {question}\n💰 الجائزة: {prize} دينار"
    
    elif game_type == "mcq":
        question = item["question"]
        options = item["options"]
        answer = item["correct"]   # مثلاً "أ" أو "ب"
        opts_text = "\n".join([f"{chr(1575+i)}. {opt}" for i, opt in enumerate(options)])  # أ، ب، ج، د
        display = f"🔘 *اختر الإجابة الصحيحة:*\n{question}\n\n{opts_text}\n💰 الجائزة: {prize} دينار\nأرسل الحرف (أ، ب، ج، د)"
    
    elif game_type == "speed_words":
        word = item["word"]
        answer = item["reversed"]
        display = f"⚡ *لعبة السرعة:* اكتب معكوس الكلمة التالية:\n`{word}`\n💰 الجائزة: {prize} دينار"
    
    elif game_type == "proverbs":
        partial = item["partial"]
        answer = item["complete"]
        display = f"📜 *أكمل المثل:* {partial}\n💰 الجائزة: {prize} دينار"
    
    elif game_type == "luck_boxes":
        # صناديق الحظ: الإجابة ستكون رقم الصندوق
        answer = "box"   # سيتم التحقق بشكل خاص
        boxes = []
        for i in range(1, 6):
            box_data = next((b for b in games_data["luck_boxes"] if b.get("box") == i), None)
            if box_data:
                boxes.append(f"📦 {i} ({box_data.get('min',0)}-{box_data.get('max',0)})")
            else:
                boxes.append(f"📦 {i}")
        display = f"🎁 *صناديق الحظ*\nاختر صندوقاً:\n" + "\n".join(boxes) + "\n💰 الجائزة: تختلف حسب الصندوق\nأرسل رقم الصندوق (1-5)"
    
    else:
        return None
    
    return {
        "type": game_type,
        "question": question,
        "answer": str(answer).strip().lower(),
        "display_text": display,
        "item": item,
        "prize": prize
    }

async def save_game_session(chat_id: int, message_id: int, game_type: str, question: str, answer: str, prize: int):
    """حفظ جلسة لعبة نشطة في قاعدة البيانات"""
    await db.execute("""
        INSERT INTO game_sessions (chat_id, message_id, game_type, question, answer, prize_money, status)
        VALUES ($1, $2, $3, $4, $5, $6, 'waiting')
    """, chat_id, message_id, game_type, question, answer, prize)

async def get_game_session(chat_id: int, message_id: int):
    """استرجاع جلسة لعبة من قاعدة البيانات"""
    row = await db.fetchrow(
        "SELECT * FROM game_sessions WHERE chat_id=$1 AND message_id=$2",
        chat_id, message_id
    )
    return dict(row) if row else None

async def update_game_session_status(chat_id: int, message_id: int, status: str):
    """تحديث حالة الجلسة (انتهت، فاز أحدهم)"""
    await db.execute(
        "UPDATE game_sessions SET status=$1 WHERE chat_id=$2 AND message_id=$3",
        status, chat_id, message_id
    )

async def check_answer(chat_id: int, message_id: int, user_answer: str):
    """التحقق من إجابة المستخدم: تعيد الجائزة إذا كانت صحيحة، 0 إذا خطأ، None إذا لا توجد جلسة"""
    session = await get_game_session(chat_id, message_id)
    if not session or session['status'] != 'waiting':
        return None
    # معالجة خاصة لصناديق الحظ
    if session['game_type'] == "luck_boxes":
        try:
            box_num = int(user_answer.strip())
            if 1 <= box_num <= 5:
                # البحث عن بيانات الصندوق من ملف luck_boxes.json
                import json, os
                from config import DATA_DIR
                luck_file = os.path.join(DATA_DIR, "luck_boxes.json")
                if os.path.exists(luck_file):
                    with open(luck_file, "r", encoding="utf-8") as f:
                        boxes = json.load(f)
                    for b in boxes:
                        if b.get("box") == box_num:
                            prize = random.randint(b.get("min", 10), b.get("max", 100))
                            await update_game_session_status(chat_id, message_id, 'finished')
                            return prize
                # إذا لم يوجد ملف، جائزة عشوائية بسيطة
                prize = random.randint(10, 200)
                await update_game_session_status(chat_id, message_id, 'finished')
                return prize
            else:
                return 0
        except:
            return 0
    # المقارنة العادية
    correct = user_answer.strip().lower() == session['answer']
    if correct:
        await update_game_session_status(chat_id, message_id, 'finished')
        return session['prize_money']
    return 0

# تحميل الألعاب عند بدء تشغيل الوحدة
load_all_games()
