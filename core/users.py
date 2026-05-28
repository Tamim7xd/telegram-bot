from db import db

conn, c = db()

TITLES = [
"🌱 مبتدئ","⚡ متعلم","🔥 نشيط","🚀 متقدم","🎯 محترف",
"⭐ مميز","👑 قائد","💎 خبير","🏆 أسطورة","🌌 أسطوري",
"⚔️ مقاتل","🛡️ فارس","🔥 وحش","🚀 نجم","🎯 ذكي",
"🧠 عبقري","👑 ملك","💎 سيد","🏆 بطل","🌌 خالق",
"⚡ إعصار","🔥 ناري","🚀 صاروخ","🎯 دقيق","👑 قائد عظيم",
"💎 أسطورة","🏆 ملك اللعبة","🌌 روح","⚡ محطم","🔥 قوي",
"🚀 سريع","🎯 محترف","👑 ملك الأساطير","💎 مجد","🏆 عليا",
"🌌 لا يُهزم","⚡ وحش","🔥 أسطوري","🚀 نجم الكون","🎯 عقل خارق",
"👑 ملك الملوك","💎 خالد","🏆 قوة","🌌 نهائي","⚡ ظل",
"🔥 تحدي","🚀 مستقبل","🎯 استراتيجي","👑 أسطورة","💎 الكيان"
]

def register(u):
    c.execute("SELECT user_id FROM users WHERE user_id=?", (u.id,))
    if not c.fetchone():
        c.execute("INSERT INTO users VALUES (?,?,?,?, 'user',0)",
                  (u.id, u.first_name, 0, 0))
        conn.commit()

def add_xp(uid, xp):
    c.execute("UPDATE users SET xp = xp + ? WHERE user_id=?", (xp, uid))
    conn.commit()

def get(uid):
    c.execute("SELECT * FROM users WHERE user_id=?", (uid,))
    return c.fetchone()

def get_title(xp):
    level = xp // 200
    return TITLES[level] if level < len(TITLES) else f"👑 أسطورة ({level})"
