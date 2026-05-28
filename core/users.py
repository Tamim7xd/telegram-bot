from db import db

conn, c = db()

# 🏆 50 لقب فخم جدًا
TITLES = [
"🌱 مبتدئ","⚡ متعلم","🔥 نشيط","🚀 متقدم","🎯 محترف",
"⭐ مميز","👑 قائد","💎 خبير","🏆 أسطورة","🌌 أسطوري",
"⚔️ محارب","🛡️ فارس","🔥 مقاتل","🚀 نجم صاعد","🎯 ذكي",
"🧠 عبقري","👑 ملك","💎 سيد الذكاء","🏆 بطل","🌌 خالق",
"⚡ إعصار","🔥 ناري","🚀 سريع","🎯 دقيق","👑 قائد عظيم",
"💎 أسطورة ذكية","🏆 ملك اللعبة","🌌 روح القتال","⚡ محطم","🔥 قوي",
"🚀 صاروخ","🎯 محترف جدًا","👑 ملك الأساطير","💎 سيد المجد","🏆 أسطورة عليا",
"🌌 لا يُهزم","⚡ وحش","🔥 مقاتل أسطوري","🚀 نجم الكون","🎯 عقل خارق",
"👑 ملك الملوك","💎 أسطورة خالدة","🏆 قوة مطلقة","🌌 أسطورة نهائية","⚡ الظل",
"🔥 سيد التحدي","🚀 قائد المستقبل","🎯 استراتيجي","👑 خالد","💎 الكيان"
]

def register(u):
    c.execute("SELECT user_id FROM users WHERE user_id=?", (u.id,))
    if not c.fetchone():
        c.execute("INSERT INTO users VALUES (?,?,?,?, 'user',0)",
                  (u.id, u.first_name, 0, 0))
        conn.commit()

def get(uid):
    c.execute("SELECT * FROM users WHERE user_id=?", (uid,))
    return c.fetchone()

def add_xp(uid, xp):
    c.execute("UPDATE users SET xp = xp + ? WHERE user_id=?", (xp, uid))
    conn.commit()

def get_title(xp):
    level = xp // 200
    if level >= len(TITLES):
        return f"👑 أسطورة مطلقة ({level})"
    return TITLES[level]
