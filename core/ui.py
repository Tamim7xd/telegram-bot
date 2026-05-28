u = get(uid)

if not u:
    
    return

money = format_iq_money(u[3] or 0)
messages = u[2] or 0
level = u[4] or 1
title = u[8] or "بدون لقب"

banned = u[10] if len(u) > 10 else 0
muted = u[11] if len(u) > 11 else 0

text = f"""
━━━━━━━━━━━━━━
👤 ملف العضو
━━━━━━━━━━━━━━

🆔 ID: {u[0]}
👤 الاسم: {u[1]}

💰 المال:
{money}

📨 عدد الرسائل:
{messages:,}

⭐ المستوى:
{level}

🏆 اللقب:
{title}

━━━━━━━━━━━━━━
📊 الحالة

🚫 الحظر: {'❌ محظور' if banned else '✅ آمن'}
🔇 الكتم: {'🔇 مكتوم' if muted else '🔊 حر'}

━━━━━━━━━━━━━━
"""

await query.edit_message_text(text)
