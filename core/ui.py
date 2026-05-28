u = get(uid)

if not u:
    await query.edit_message_text("❌ المستخدم غير موجود")
    return

await query.edit_message_text(
f"""
━━━━━━━━━━━━━━
👤 ملف العضو
━━━━━━━━━━━━━━

🆔 ID: {u[0]}
👤 الاسم: {u[1]}

💰 المال:
{format_iq_money(u[3] or 0)}

📨 عدد الرسائل:
{u[2] or 0:,}

⭐ المستوى:
{u[4] or 1}

🏆 اللقب:
{u[8] or "بدون لقب"}

━━━━━━━━━━━━━━
📊 الحالة

🚫 الحظر: {'❌ محظور' if u[10] else '✅ آمن'}
🔇 الكتم: {'🔇 مكتوم' if u[11] else '🔊 حر'}

━━━━━━━━━━━━━━
"""
)
