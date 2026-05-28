from core.users import (
    get_title,
    progress_bar,
    next_goal,
    format_money
)


def profile_text(user):

    messages = user[2]

    money = user[3]

    warnings = user[4]

    rewards = user[5]

    custom = user[6]

    locked = user[7]

    title = get_title(
        messages,
        custom,
        locked
    )

    target = next_goal(messages)

    remain = target - messages

    return f"""
👤 الاسم:
{user[1]}

💰 الفلوس:
{format_money(money)} دينار

🏆 اللقب:
{title}

💬 الرسائل:
{messages}

⚠️ التنبيهات:
{warnings}

🎁 المكافآت:
{rewards}

📈 التقدم:
{progress_bar(messages)}

🚀 باقي {remain} رسالة للقب التالي
"""
