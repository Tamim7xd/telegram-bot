from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup
)

from db import c, conn

from core.users import (
    get,
    format_money,
    get_title
)

# ================= USERS PAGE =================
def users_page(page=0):

    limit = 5

    offset = page * limit

    c.execute("""
    SELECT user_id,name
    FROM users
    ORDER BY messages DESC
    LIMIT ?
    OFFSET ?
    """, (limit, offset))

    rows = c.fetchall()

    keyboard = []

    for uid, name in rows:

        keyboard.append([
            InlineKeyboardButton(
                name,
                callback_data=f"user_{uid}_{page}"
            )
        ])

    nav = []

    if page > 0:

        nav.append(
            InlineKeyboardButton(
                "⬅ السابق",
                callback_data=f"users_{page-1}"
            )
        )

    if len(rows) >= limit:

        nav.append(
            InlineKeyboardButton(
                "➡ التالي",
                callback_data=f"users_{page+1}"
            )
        )

    if nav:
        keyboard.append(nav)

    keyboard.append([
        InlineKeyboardButton(
            "❌ إغلاق",
            callback_data="close"
        )
    ])

    return InlineKeyboardMarkup(keyboard)


# ================= USER PANEL =================
def user_panel(uid, page):

    user = get(uid)

    if not user:
        return None, None

    title = get_title(
        user[2],
        user[6],
        user[7]
    )

    text = f"""
👤 العضو:
{user[1]}

💰 الفلوس:
{format_money(user[3])}

🏆 اللقب:
{title}

💬 الرسائل:
{user[2]}

⚠️ التنبيهات:
{user[4]}

🎁 المكافآت:
{user[5]}
"""

    kb = [

        [
            InlineKeyboardButton(
                "💰 إضافة فلوس",
                callback_data=f"addmoney_{uid}"
            )
        ],

        [
            InlineKeyboardButton(
                "💸 خصم فلوس",
                callback_data=f"removemoney_{uid}"
            )
        ],

        [
            InlineKeyboardButton(
                "🏆 تعديل لقب",
                callback_data=f"title_{uid}"
            )
        ],

        [
            InlineKeyboardButton(
                "⚠️ إرسال تنبيه",
                callback_data=f"warn_{uid}"
            )
        ],

        [
            InlineKeyboardButton(
                "⬅ رجوع",
                callback_data=f"users_{page}"
            ),

            InlineKeyboardButton(
                "❌ إغلاق",
                callback_data="close"
            )
        ]
    ]

    return text, InlineKeyboardMarkup(kb)
