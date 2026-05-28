from db import c, conn, now
import time
import random

def reg(u):
    c.execute("SELECT user_id FROM users WHERE user_id=?", (u.id,))
    if not c.fetchone():
        c.execute("""
        INSERT INTO users VALUES (?,?,?,?,?,?,?,?)
        """, (u.id, u.first_name, 0, 0, "مبتدئ", now(), 0, 0))
        conn.commit()

def get(uid):
    c.execute("SELECT * FROM users WHERE user_id=?", (uid,))
    return c.fetchone()

def is_banned(uid):
    c.execute("SELECT banned FROM users WHERE user_id=?", (uid,))
    r = c.fetchone()
    return r and r[0] == 1

def is_muted(uid):
    c.execute("SELECT muted_until FROM users WHERE user_id=?", (uid,))
    r = c.fetchone()
    return r and r[0] > int(time.time())


# 🔥 50 لقب
TITLES = [
"⚔️ المحارب","🔥 الأسطورة","👑 الملك","💎 الماسي","🚀 الصاروخ",
"🐉 التنين","⚡ السريع","🎯 القناص","🧠 الذكي","🦁 الأسد",
"🌟 النجم","💀 القوي","🛡️ الحارس","🏆 البطل","🎮 اللاعب",
"🌈 المميز","🧿 الحامي","👾 الغامض","💫 الساطع","⚙️ التقني",
"🧭 المستكشف","🏹 الرامي","🪐 الكوني","🌊 البحار","⛰️ الجبلي",
"🧨 المدمر","🧑‍💻 المبرمج","📡 المراقب","🔮 العراف","🧿 الأسطوري",
"⚔️ المحارب الأول","🔥 نجم النار","💎 الماس الملكي","👑 إمبراطور",
"🚀 قائد السرعة","🧠 العبقري","⚡ برق","🌟 أسطورة المجتمع"
]

# ❓ أسئلة (يمكن توسعتها إلى 100 بسهولة)
QUESTIONS = [
{"q":"ما هي عاصمة العراق؟","a":"بغداد"},
{"q":"كم عدد أيام الأسبوع؟","a":"7"},
{"q":"ما هو لون السماء؟","a":"أزرق"},
{"q":"ما هو أكبر كوكب؟","a":"المشتري"},
{"q":"كم عدد القارات؟","a":"7"},
]

def get_question():
    return random.choice(QUESTIONS)


def handle_user(text, update):

    u = update.effective_user
    reg(u)

    c.execute("UPDATE users SET messages=messages+1 WHERE user_id=?", (u.id,))
    conn.commit()

    d = get(u.id)
    t = text.lower().strip()

    if t in ["فلوسي","راتبي","مصاري","فوس"]:
        return f"💰 فلوسك: {d[2]}"

    if t in ["رسائلي","رسايل"]:
        return f"💬 رسائلك: {d[3]}"

    if t in ["لقبي","لقب"]:
        return f"🏷️ لقبك: {d[4]}"

    if t in ["معلوماتي","معلومات"]:
        return f"""
👤 الاسم: {d[1]}
💰 فلوسك: {d[2]}
💬 رسائلك: {d[3]}
🏷️ لقبك: {d[4]}
"""