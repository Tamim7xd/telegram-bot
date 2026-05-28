import random
from db import db

conn, c = db()

QUESTIONS = [
# 🌍 جغرافيا
("ما عاصمة العراق؟","بغداد"),
("أكبر قارة؟","آسيا"),

# 🔬 علوم
("ما هو غاز التنفس للبشر؟","الأوكسجين"),
("كم عدد كواكب المجموعة الشمسية؟","8"),

# ⚽ رياضة
("كم لاعب في كرة القدم؟","11"),
("أين أقيم كأس العالم 2022؟","قطر"),

# 📚 ثقافة
("من كتب ألف ليلة وليلة؟","غير معروف"),
("أول دولة استخدمت الورق؟","الصين"),

# 🕌 دين
("كم عدد الصلوات اليومية؟","5"),
("في أي شهر رمضان؟","9")
]

def random_q():
    return random.choice(QUESTIONS)

def set_q(uid, ans):
    c.execute("REPLACE INTO questions VALUES (?,?)", (uid, ans))
    conn.commit()

def get_q(uid):
    c.execute("SELECT answer FROM questions WHERE user_id=?", (uid,))
    return c.fetchone()

def del_q(uid):
    c.execute("DELETE FROM questions WHERE user_id=?", (uid,))
    conn.commit()
