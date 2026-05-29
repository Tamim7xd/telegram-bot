from aiogram import Dispatcher
from aiogram.types import Message
from config import ADMIN_IDS, CURRENCY_NAME, XP_PER_MESSAGE
from _core.users import update_user_money, get_user, set_user_status, get_or_create_user
from _core.xp import add_xp, get_xp_progress
from _core.games import cmd_game
from _core.titles import set_user_title
from _core.notify import bot
from db import db
from datetime import datetime, timedelta

# دوال إحصائيات بسيطة
async def get_user_stats(user_id: int):
    row = await db.fetchrow("SELECT * FROM user_stats WHERE user_id = $1", user_id)
    if not row:
        await db.execute("INSERT INTO user_stats (user_id) VALUES (?)", user_id)
        row = await db.fetchrow("SELECT * FROM user_stats WHERE user_id = $1", user_id)
    return row

async def update_user_stats(user_id: int, field: str, value=1, extra=None):
    if field in ["total_messages", "total_warns", "total_mutes", "total_bans", "total_kicks", "total_deductions"]:
        await db.execute(f"UPDATE user_stats SET {field} = {field} + ? WHERE user_id = ?", value, user_id)
    elif field == "last_deduction" and extra:
        amount, reason = extra
        await db.execute("UPDATE user_stats SET last_deduction_amount = ?, last_deduction_reason = ?, last_deduction_at = CURRENT_TIMESTAMP WHERE user_id = ?", amount, reason, user_id)

# إشعارات
async def send_admin_notification(chat_id, admin_name, target_name, action, detail=""):
    text = f"🔔 *{action}*\n👤 المشرف: {admin_name}\n👥 المستخدم: {target_name}\n📝 {detail}"
    await bot.send_message(chat_id, text, parse_mode="Markdown")

# أوامر $ (الأدمن)
async def handle_admin_commands(message: Message):
    if not message.reply_to_message:
        return
    uid = message.from_user.id
    if uid not in ADMIN_IDS:
        return
    target = message.reply_to_message.from_user
    text = message.text.strip()
    chat_id = message.chat.id
    admin_name = message.from_user.full_name
    target_name = target.full_name

    if text.startswith("$خصم"):
        parts = text.split()
        if len(parts) >= 2 and parts[1].isdigit():
            amount = int(parts[1])
            reason = parts[2] if len(parts) > 2 else "خصم"
            await update_user_money(target.id, -amount, reason, uid)
            await message.reply(f"✅ خصم {amount} من {target_name}")
            await send_admin_notification(chat_id, admin_name, target_name, "💰 خصم", f"{amount} {CURRENCY_NAME}\nالسبب: {reason}")
    elif text.startswith("$اعطاء"):
        parts = text.split()
        if len(parts) >= 2 and parts[1].isdigit():
            amount = int(parts[1])
            reason = parts[2] if len(parts) > 2 else "مكافأة"
            await update_user_money(target.id, amount, reason, uid)
            await message.reply(f"✅ إضافة {amount} إلى {target_name}")
            await send_admin_notification(chat_id, admin_name, target_name, "💰 إضافة", f"+{amount} {CURRENCY_NAME}")
    elif text.startswith("$كتم"):
        await set_user_status(target.id, "muted")
        await message.reply(f"🔇 تم كتم {target_name}")
        await send_admin_notification(chat_id, admin_name, target_name, "🔇 كتم", "")
    elif text == "$فك كتم":
        await set_user_status(target.id, "active")
        await message.reply(f"🔈 فك الكتم عن {target_name}")
    elif text.startswith("$حظر"):
        await set_user_status(target.id, "banned")
        await message.reply(f"🚫 حظر {target_name}")
    elif text == "$فك حظر":
        await set_user_status(target.id, "active")
        await message.reply(f"✅ فك الحظر عن {target_name}")
    elif text.startswith("$طرد"):
        await message.reply(f"👢 طرد {target_name}")
        try:
            await message.chat.ban_member(target.id)
            await message.chat.unban_member(target.id)
        except: pass
    elif text.startswith("$لقب"):
        new_title = text[5:].strip()
        if new_title:
            await set_user_title(target.id, new_title)
            await message.reply(f"🏷️ لقب {target_name} → {new_title}")
    elif text == "$سجل":
        rows = await db.fetch("SELECT * FROM economy_log WHERE admin_id = ? ORDER BY timestamp DESC LIMIT 10", uid)
        if rows:
            log = "📜 سجلك:\n" + "\n".join([f"{r['amount']} - {r['reason']}" for r in rows])
            await message.reply(log)

# أوامر #
async def handle_member_commands(message: Message):
    text = message.text.strip()
    uid = message.from_user.id
    # تأكد من وجود المستخدم في قاعدة البيانات
    await get_or_create_user(message.from_user)

    if text in ["#ملفي", "#حسابي", "#معلوماتي"]:
        user = await get_user(uid)
        stats = await get_user_stats(uid)
        progress = await get_xp_progress(uid)
        reply = f"👤 {user['full_name']}\n💰 {user['money']}\n⭐ XP: {user['xp']}\n📊 المستوى: {user['level']}\n🏷️ اللقب: {user['title'] or 'لا يوجد'}\n📨 الرسائل: {stats['total_messages']}\n{progress['bar']} {progress['percent']}%"
        await message.reply(reply)
    elif text in ["#فلوس", "#فلوسي"]:
        user = await get_user(uid)
        await message.reply(f"💰 رصيدك: {user['money']}")
    elif text in ["#لعبة", "#العب", "#العاب"]:
        await cmd_game(message)
    elif text in ["#مستواي", "#نقاطي"]:
        progress = await get_xp_progress(uid)
        await message.reply(f"📊 المستوى {progress['level']}\n{progress['bar']} {progress['percent']}%")
    elif text in ["#شراء", "#محل", "#سوق"]:
        # قائمة بسيطة بالرتب
        items = await db.fetch("SELECT name, price FROM shop_items ORDER BY rank_level")
        if items:
            txt = "🏪 *السوق*\n"
            for it in items:
                txt += f"• {it['name']} - {it['price']} {CURRENCY_NAME}\n"
            txt += "\nاستخدم #شراء <اسم الرتبة> لشرائها"
            await message.reply(txt, parse_mode="Markdown")
        else:
            await message.reply("السوق فارغ حالياً.")

# إضافة XP
async def add_xp_on_message(message: Message):
    await get_or_create_user(message.from_user)  # تسجيل تلقائي
    if not message.text or message.text.startswith(("#", "$")):
        return
    await add_xp(message.from_user.id, XP_PER_MESSAGE, message.chat.id, message.from_user.full_name)
    await update_user_stats(message.from_user.id, 'total_messages')

def register_event_handlers(dp: Dispatcher):
    dp.message.register(handle_admin_commands, lambda m: m.text and m.text.startswith("$"))
    dp.message.register(handle_member_commands, lambda m: m.text and m.text.startswith("#"))
    dp.message.register(add_xp_on_message)
