from db import conn, c


TITLES = [

"🌱 المبتدئ",
"⚡ النشيط",
"🔥 المتفاعل",
"🚀 المتطور",
"🎯 المحترف",
"⭐ المميز",
"👑 القائد",
"💎 الخبير",
"🏆 الأسطورة",
"🌌 سيد المجرة",

"⚔️ المحارب",
"🛡️ الحامي",
"🐉 قاتل التنانين",
"🌋 سيد النار",
"❄️ سيد الجليد",
"🌪️ سيد العواصف",
"☄️ الصاعقة",
"🦅 الصقر الذهبي",
"🐺 الذئب الأسود",
"🦂 العقرب القاتل",

"👁️ الحارس الأبدي",
"🗡️ سيد السيوف",
"🏹 القناص",
"⚜️ النبيل",
"👹 المدمر",
"💀 سيد الظلام",
"☠️ ملك الرعب",
"👑 الإمبراطور",
"🌠 سيد النجوم",
"🌑 فارس الليل",

"🔱 سيد البحار",
"⚡ البرق المدمر",
"🌌 المسافر الكوني",
"🪐 حاكم الكواكب",
"🦁 الأسد الملك",
"🐲 التنين العظيم",
"🔥 اللهب الأزرق",
"🌙 القمر الدموي",
"🌞 شمس المعركة",
"🧊 ملك الصقيع",

"🎖️ الجنرال",
"🏅 القائد الأعلى",
"⚔️ الفاتح",
"💥 محطم الأساطير",
"🛸 الغازي الفضائي",
"🌐 سيد الأكوان",
"👁️‍🗨️ عين الحقيقة",
"🔮 الساحر الأعظم",
"💫 سيد الزمن",
"🚀 الأسطورة المطلقة"

] * 5


# ================= REGISTER =================
def register(user):

    c.execute(
        "SELECT user_id FROM users WHERE user_id=?",
        (user.id,)
    )

    if not c.fetchone():

        c.execute("""
        INSERT INTO users(
            user_id,
            name
        )
        VALUES (?,?)
        """, (
            user.id,
            user.first_name
        ))

        conn.commit()


# ================= GET =================
def get(uid):

    c.execute(
        "SELECT * FROM users WHERE user_id=?",
        (uid,)
    )

    return c.fetchone()


# ================= ADD MESSAGE =================
def add_message(uid):

    c.execute("""
    UPDATE users

    SET
        messages = messages + 1,
        money = money + 250

    WHERE user_id=?
    """, (uid,))

    conn.commit()


# ================= MONEY =================
def format_money(amount):

    return f"{amount:,}"


# ================= TITLE =================
def get_title(messages, custom="", locked=0):

    if locked and custom:
        return custom

    if messages < 100:
        return "بدون لقب"

    level = 1 + ((messages - 100) // 250)

    if level >= len(TITLES):
        level = len(TITLES) - 1

    return TITLES[level]


# ================= NEXT GOAL =================
def next_goal(messages):

    if messages < 100:
        return 100

    level = ((messages - 100) // 250) + 1

    return 100 + (level * 250)


# ================= PROGRESS =================
def progress_bar(messages):

    target = next_goal(messages)

    previous = target - 250 if target > 100 else 0

    current = messages - previous

    needed = target - previous

    percent = int((current / needed) * 10)

    if percent > 10:
        percent = 10

    return (
        "█" * percent
        +
        "░" * (10 - percent)
    )
