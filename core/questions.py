import random
from db import db

conn, c = db()

QUESTIONS = [
("ما عاصمة العراق؟","بغداد"),
("أكبر كوكب؟","المشتري"),
("كم عدد القارات؟","7"),
("كم عدد الصلوات؟","5"),
("ما غاز التنفس؟","الأوكسجين"),
("كم لاعب كرة القدم؟","11"),
("أين تقع مصر؟","افريقيا"),
("ما أكبر محيط؟","الهادئ"),
("ما لغة اليابان؟","اليابانية")
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
