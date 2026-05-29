from aiogram import Dispatcher
from aiogram.types import Message
from config import ADMIN_IDS, CURRENCY_NAME, XP_PER_MESSAGE
from _core.users import update_user_money, get_user, set_user_status
from _core.xp import add_xp, get_xp_progress
from _core.games import cmd_game
from _core.titles import set_user_title
from _core.notify import bot
from db import db

# دالة إرسال إشعار إداري للمجموعة
async def send_admin_notification(chat_id: int, admin_name: str, target_name: str, action: str, detail: str = ""):
    text = f"""╭━━━━━━━━━━━━━━━━━━━━━━━━━━╮
┃ 🔔 *إشـارة إداريـة* 🔔
╰━━━━━━━━━━━━━━━━━━━━━━━━━━╯

👤 *المشرف:* {admin_name}
👥 *المستخدم:* {target_name}
⚙️ *الإجراء:* {action}
📝 *التفاصيل:* {detail}

🕒 *الوقت:* الآن
━━━━━━━━━━━━━━━━━━━━━━━━━━"""
    await bot.send_message(chat_id, text, parse_mode="Markdown")

# أوامر الأدمن بالرد ($)
async def handle_admin_commands(message: Message):
    if not message.reply_to_message:
        return
    if message.from_user.id not in ADMIN_IDS:
        return
    
    admin = message.from_user
    target = message.reply_to_message.from_user
    text = message.text.strip()
    chat_id = message.chat.id
    admin_name = admin.full_name
    target_name = target.full_name
    
    # $خصم 50 سبب
    if text.startswith("$خصم"):
        parts = text.split(maxsplit=2)
        if len(parts) >= 2 and parts[1].isdigit():
            amount = int(parts[1])
            reason = parts[2] if len(parts) > 2 else "لا يوجد سبب"
            await update_user_money(target.id, -amount, reason, admin.id)
            await message.reply(f"✅ تم خصم {amount} {CURRENCY_NAME} من {target_name}")
            await send_admin_notification(chat_id, admin_name, target_name, "💰 خصم رصيد", f"-{amount} {CURRENCY_NAME}\nالسبب: {reason}")
        else:
            await message.reply("❌ استخدم: $خصم 50 سبب")
    
    # $اعطاء 100 مكافأة
    elif text.startswith("$اعطاء") or text.startswith("$إعطاء"):
        parts = text.split(maxsplit=2)
        if len(parts) >= 2 and parts[1].isdigit():
            amount = int(parts[1])
            reason = parts[2] if len(parts) > 2 else "مكافأة"
            await update_user_money(target.id, amount, reason, admin.id)
            await message.reply(f"✅ تم إضافة {amount} {CURRENCY_NAME} إلى {target_name}")
            await send_admin_notification(chat_id, admin_name, target_name, "💰 إضافة رصيد", f"+{amount} {CURRENCY_NAME}\nالسبب: {reason}")
        else:
            await message.reply("❌ استخدم: $اعطاء 100 سبب")
    
    # $تحذير سبب
    elif text.startswith("$تحذير"):
        reason = text[8:].strip() or "لا يوجد سبب"
        user = await get_user(target.id)
        warnings = user['warnings'] + 1
        await db.execute("UPDATE users SET warnings = $1 WHERE telegram_id = $2", warnings, target.id)
        await message.reply(f"⚠️ تم تحذير {target_name} (التحذير {warnings}/3)\nالسبب: {reason}")
        await send_admin_notification(chat_id, admin_name, target_name, "⚠️ تحذير", f"التحذير {warnings}/3\nالسبب: {reason}")
        if warnings >= 3:
            await set_user_status(target.id, "banned")
            await message.reply(f"🚫 تم حظر {target_name} تلقائياً بسبب 3 تحذيرات")
    
    # $كتم 10m سبب
    elif text.startswith("$كتم"):
        parts = text.split(maxsplit=2)
        duration = parts[1] if len(parts) >= 2 else "30m"
        reason = parts[2] if len(parts) > 2 else "لا يوجد سبب"
        await set_user_status(target.id, "muted")
        await message.reply(f"🔇 تم كتم {target_name} لمدة {duration}")
        await send_admin_notification(chat_id, admin_name, target_name, "🔇 كتم", f"لمدة {duration}\nالسبب: {reason}")
    
    # $فك كتم
    elif text == "$فك كتم":
        await set_user_status(target.id, "active")
        await message.reply(f"🔈 تم فك الكتم عن {target_name}")
        await send_admin_notification(chat_id, admin_name, target_name, "🔈 فك كتم", "تم فك الكتم")
    
    # $حظر سبب
    elif text.startswith("$حظر"):
        reason = text[5:].strip() or "لا يوجد سبب"
        await set_user_status(target.id, "banned")
        await message.reply(f"🚫 تم حظر {target_name}")
        await send_admin_notification(chat_id, admin_name, target_name, "🚫 حظر", f"السبب: {reason}")
    
    # $فك حظر
    elif text == "$فك حظر":
        await set_user_status(target.id, "active")
        await message.reply(f"✅ تم فك الحظر عن {target_name}")
        await send_admin_notification(chat_id, admin_name, target_name, "✅ فك حظر", "")
    
    # $طرد سبب
    elif text.startswith("$طرد"):
        reason = text[5:].strip() or "لا يوجد سبب"
        await message.reply(f"👢 تم طرد {target_name}")
        await send_admin_notification(chat_id, admin_name, target_name, "🗑️ طرد", f"السبب: {reason}")
        try:
            await message.chat.ban_member(target.id)
            await message.chat.unban_member(target.id)
        except:
            pass
    
    # $لقب اسم
    elif text.startswith("$لقب"):
        new_title = text[5:].strip()
        if new_title:
            await set_user_title(target.id, new_title)
            await message.reply(f"🏷️ تم منح اللقب '{new_title}' إلى {target_name}")
            await send_admin_notification(chat_id, admin_name, target_name, "🏷️ تغيير لقب", f"اللقب الجديد: {new_title}")
        else:
            await message.reply("❌ استخدم: $لقب بطل")
    
    # $سجل
    elif text == "$سجل":
        rows = await db.fetch("SELECT * FROM economy_log WHERE admin_id = $1 ORDER BY timestamp DESC LIMIT 10", admin.id)
        if rows:
            log_text = "📜 *آخر عملياتك:*\n"
            for row in rows:
                log_text += f"• {row['amount']} {CURRENCY_NAME} للمستخدم {row['user_id']} - {row['reason']}\n"
            await message.reply(log_text, parse_mode="Markdown")
        else:
            await message.reply("📭 لا توجد عمليات مسجلة لك.")

# أوامر الأعضاء (#)
async def handle_member_commands(message: Message):
    text = message.text.strip()
    user_id = message.from_user.id
    
    # #ملفي, #حسابي, #معلوماتي, #ملف
    if text in ["#ملفي", "#حسابي", "#معلوماتي", "#معلومات", "#ملف"]:
        user = await get_user(user_id)
        progress = await get_xp_progress(user_id)
        reply = f"""╭━━━━━━━━━━━━━━━━━━━━━━╮
┃ 👤 *الملف الشخصي* 👤
╰━━━━━━━━━━━━━━━━━━━━━━╯

✨ *الاسم:* {user['full_name']}
🆔 *المعرف:* @{user['username'] or 'لا يوجد'}

━━━━━━━━━━━━━━━━━━━━━━
💰 *الرصيد:* {user['money']} {CURRENCY_NAME}
🏆 *اللقب:* {user['title'] or 'لا يوجد'}
⭐ *النقاط (XP):* {user['xp']}
📊 *المستوى:* {user['level']}

📈 *شريط التقدم:*
{progress['bar']} {progress['percent']}%

⏳ *المتبقي للمستوى التالي:* {progress['remaining']} XP

━━━━━━━━━━━━━━━━━━━━━━
🎮 *نقاط الألعاب:* {user['game_points']}
🏅 *الفوز في الألعاب:* {user['wins']}"""
        await message.reply(reply, parse_mode="Markdown")
    
    # #فلوس, #فلوسي, #رصيدي
    elif text in ["#فلوس", "#فلوسي", "#رصيدي"]:
        user = await get_user(user_id)
        await message.reply(f"💰 رصيدك الحالي: {user['money']} {CURRENCY_NAME}")
    
    # #لقب, #لقبي, #اللقب
    elif text in ["#لقب", "#لقبي", "#اللقب"]:
        user = await get_user(user_id)
        title = user['title'] or "لا يوجد"
        await message.reply(f"🏷️ لقبك: {title}")
    
    # #لعبة, #العب, #العاب
    elif text in ["#لعبة", "#العب", "#العاب"]:
        await cmd_game(message)
    
    # #مستواي, #لـيفلي, #نقاطي
    elif text in ["#مستواي", "#لـيفلي", "#نقاطي"]:
        user = await get_user(user_id)
        progress = await get_xp_progress(user_id)
        await message.reply(f"📊 *المستوى {user['level']}*\n{progress['bar']} {progress['percent']}%\n{progress['remaining']} XP للمستوى التالي", parse_mode="Markdown")

# إضافة XP عند كل رسالة عادية
async def add_xp_on_message(message: Message):
    if not message.text:
        return
    if message.text.startswith(("#", "$")):
        return
    if message.from_user.id in ADMIN_IDS:
        return
    await add_xp(message.from_user.id, XP_PER_MESSAGE, message.chat.id, message.from_user.full_name)

def register_event_handlers(dp: Dispatcher):
    dp.message.register(handle_admin_commands, lambda msg: msg.text and msg.text.startswith("$"))
    dp.message.register(handle_member_commands, lambda msg: msg.text and msg.text.startswith("#"))
    dp.message.register(add_xp_on_message)
