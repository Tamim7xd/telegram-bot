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
import asyncio

# ========== إحصائيات المستخدم ==========
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
        amt, rsn = extra
        await db.execute("UPDATE user_stats SET last_deduction_amount = ?, last_deduction_reason = ?, last_deduction_at = CURRENT_TIMESTAMP WHERE user_id = ?", amt, rsn, user_id)

# ========== إشعار إداري متطور ==========
async def send_admin_notification(chat_id, admin_name, target_name, action, detail=""):
    border = "╭━━━━━━━━━━━━━━━━━━━━━━━━━━╮"
    text = f"""{border}
┃ 🔔 *إشـارة إداريـة* 🔔
╰━━━━━━━━━━━━━━━━━━━━━━━━━━╯

👤 *المشرف:* {admin_name}
👥 *المستخدم:* {target_name}
⚙️ *الإجراء:* {action}
📝 *التفاصيل:* {detail}
🕒 *الوقت:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
━━━━━━━━━━━━━━━━━━━━━━━━━━"""
    await bot.send_message(chat_id, text, parse_mode="Markdown")

# ========== أوامر الأدمن ($) – تنفيذ حقيقي ==========
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

    # خصم رصيد
    if text.startswith("$خصم"):
        parts = text.split(maxsplit=2)
        if len(parts) >= 2 and parts[1].isdigit():
            amt = int(parts[1])
            reason = parts[2] if len(parts) > 2 else "خصم"
            await update_user_money(target.id, -amt, reason, uid)
            await message.reply(f"✅ تم خصم {amt} {CURRENCY_NAME} من {target_name}")
            await send_admin_notification(chat_id, admin_name, target_name, "💰 خصم رصيد", f"-{amt} {CURRENCY_NAME}\nالسبب: {reason}")
            await update_user_stats(target.id, 'total_deductions', 1, (amt, reason))
        else:
            await message.reply("❌ استخدم: $خصم 50 سبب")
    # إضافة رصيد
    elif text.startswith("$اعطاء") or text.startswith("$إعطاء"):
        parts = text.split(maxsplit=2)
        if len(parts) >= 2 and parts[1].isdigit():
            amt = int(parts[1])
            reason = parts[2] if len(parts) > 2 else "مكافأة"
            await update_user_money(target.id, amt, reason, uid)
            await message.reply(f"✅ تم إضافة {amt} {CURRENCY_NAME} إلى {target_name}")
            await send_admin_notification(chat_id, admin_name, target_name, "💰 إضافة رصيد", f"+{amt} {CURRENCY_NAME}\nالسبب: {reason}")
        else:
            await message.reply("❌ استخدم: $اعطاء 100 سبب")
    # كتم (تغيير الحالة في قاعدة البيانات + محاولة كتم حقيقي عبر البوت)
    elif text.startswith("$كتم"):
        parts = text.split(maxsplit=2)
        duration_str = parts[1] if len(parts) >= 2 else "30m"
        reason = parts[2] if len(parts) > 2 else "لا يوجد سبب"
        # كتم عبر البوت (صلاحية administrator مطلوبة)
        try:
            permissions = await message.chat.get_member(bot.id)
            if permissions.is_chat_admin():
                await message.chat.restrict_member(target.id, permissions=permissions, until_date=datetime.now()+timedelta(minutes=30))
                await message.reply(f"🔇 تم كتم {target_name} لمدة {duration_str}\nالسبب: {reason}")
            else:
                await message.reply("⚠️ البوت ليس مديراً في المجموعة، لا يمكن الكتم الفعلي.")
        except Exception as e:
            await message.reply(f"❌ فشل الكتم: {e}")
        # تحديث الحالة في قاعدة البيانات
        await set_user_status(target.id, "muted")
        await send_admin_notification(chat_id, admin_name, target_name, "🔇 كتم", f"لمدة {duration_str}\nالسبب: {reason}")
        await update_user_stats(target.id, 'total_mutes')
        return
    # فك الكتم
    elif text == "$فك كتم":
        try:
            await message.chat.restrict_member(target.id, can_send_messages=True, can_send_media_messages=True, can_send_other_messages=True)
            await message.reply(f"🔈 تم فك الكتم عن {target_name}")
        except:
            await message.reply("⚠️ فشل فك الكتم، تأكد من صلاحيات البوت.")
        await set_user_status(target.id, "active")
        await send_admin_notification(chat_id, admin_name, target_name, "🔈 فك كتم", "")
        return
    # حظر
    elif text.startswith("$حظر"):
        reason = text[5:].strip() or "لا يوجد سبب"
        try:
            await message.chat.ban_member(target.id)
            await message.reply(f"🚫 تم حظر {target_name}\nالسبب: {reason}")
            await send_admin_notification(chat_id, admin_name, target_name, "🚫 حظر", reason)
            await update_user_stats(target.id, 'total_bans')
        except Exception as e:
            await message.reply(f"❌ فشل الحظر: {e}")
        await set_user_status(target.id, "banned")
        return
    # فك الحظر
    elif text == "$فك حظر":
        try:
            await message.chat.unban_member(target.id)
            await message.reply(f"✅ تم فك الحظر عن {target_name}")
        except:
            await message.reply("⚠️ فشل فك الحظر")
        await set_user_status(target.id, "active")
        await send_admin_notification(chat_id, admin_name, target_name, "✅ فك حظر", "")
        return
    # طرد
    elif text.startswith("$طرد"):
        reason = text[5:].strip() or "لا يوجد سبب"
        try:
            await message.chat.ban_member(target.id)
            await message.chat.unban_member(target.id)
            await message.reply(f"👢 تم طرد {target_name}\nالسبب: {reason}")
            await send_admin_notification(chat_id, admin_name, target_name, "🗑️ طرد", reason)
            await update_user_stats(target.id, 'total_kicks')
        except Exception as e:
            await message.reply(f"❌ فشل الطرد: {e}")
        return
    # تغيير اللقب
    elif text.startswith("$لقب"):
        new_title = text[5:].strip()
        if new_title:
            success = await set_user_title(target.id, new_title)
            if success:
                await message.reply(f"🏷️ تم منح اللقب '{new_title}' إلى {target_name}")
                await send_admin_notification(chat_id, admin_name, target_name, "🏷️ تغيير لقب", f"اللقب الجديد: {new_title}")
            else:
                await message.reply("❌ اللقب غير موجود في القائمة")
        else:
            await message.reply("❌ استخدم: $لقب بطل")
    # سجل الأدمن
    elif text == "$سجل":
        rows = await db.fetch("SELECT * FROM economy_log WHERE admin_id = ? ORDER BY timestamp DESC LIMIT 10", uid)
        if rows:
            log = "📜 *آخر عملياتك:*\n"
            for r in rows:
                log += f"• {r['amount']} {CURRENCY_NAME} - {r['reason']}\n"
            await message.reply(log, parse_mode="Markdown")
        else:
            await message.reply("📭 لا توجد عمليات مسجلة لك.")
    # معلومات المستخدم (تختفي بعد 3 ثوانٍ)
    elif text.startswith("$معلومات"):
        u = await get_user(target.id)
        if u:
            msg = await message.reply(f"📄 *معلومات {u['full_name']}*\n💰 الرصيد: {u['money']}\n⭐ XP: {u['xp']}\n📊 المستوى: {u['level']}\n🏷️ اللقب: {u['title'] or 'لا يوجد'}")
            await asyncio.sleep(3)
            await msg.delete()
            await message.delete()
        else:
            await message.reply("المستخدم غير موجود")

# ========== أوامر الأعضاء (#) مع اختفاء المعلومات ==========
async def handle_member_commands(message: Message):
    text = message.text.strip()
    uid = message.from_user.id
    await get_or_create_user(message.from_user)

    if text in ["#ملفي", "#حسابي", "#معلوماتي"]:
        user = await get_user(uid)
        stats = await get_user_stats(uid)
        progress = await get_xp_progress(uid)
        reply = f"👤 *{user['full_name']}*\n💰 {user['money']} {CURRENCY_NAME}\n⭐ XP: {user['xp']}\n📊 المستوى: {user['level']}\n🏷️ اللقب: {user['title'] or 'لا يوجد'}\n📨 الرسائل: {stats['total_messages']}\n⚠️ التحذيرات: {stats['total_warns']}\n📈 {progress['bar']} {progress['percent']}%"
        msg = await message.reply(reply, parse_mode="Markdown")
        await asyncio.sleep(3)
        await msg.delete()
        await message.delete()
    elif text in ["#فلوس", "#فلوسي"]:
        user = await get_user(uid)
        msg = await message.reply(f"💰 رصيدك: {user['money']} {CURRENCY_NAME}")
        await asyncio.sleep(3)
        await msg.delete()
    elif text in ["#لقب", "#لقبي"]:
        user = await get_user(uid)
        msg = await message.reply(f"🏷️ لقبك: {user['title'] or 'لا يوجد'}")
        await asyncio.sleep(3)
        await msg.delete()
    elif text in ["#لعبة", "#العب", "#العاب"]:
        await cmd_game(message)
    elif text in ["#مستواي", "#نقاطي"]:
        progress = await get_xp_progress(uid)
        msg = await message.reply(f"📊 المستوى {progress['level']}\n{progress['bar']} {progress['percent']}%")
        await asyncio.sleep(3)
        await msg.delete()
    elif text in ["#شراء", "#محل", "#سوق"]:
        items = await db.fetch("SELECT name, price FROM shop_items ORDER BY rank_level")
        if items:
            txt = "🏪 *السوق*\n"
            for it in items:
                txt += f"• {it['name']} - {it['price']} {CURRENCY_NAME}\n"
            txt += "\nاستخدم `#شراء <اسم الرتبة>` لشرائها"
            await message.reply(txt, parse_mode="Markdown")
        else:
            await message.reply("السوق فارغ حالياً.")
    # شراء رتبة
    elif text.startswith("#شراء"):
        parts = text.split(maxsplit=1)
        if len(parts) < 2:
            await message.reply("❌ استخدم: #شراء اسم الرتبة")
            return
        rank_name = parts[1]
        item = await db.fetchrow("SELECT * FROM shop_items WHERE name = ?", rank_name)
        if not item:
            await message.reply("❌ الرتبة غير موجودة")
            return
        user = await get_user(uid)
        if user['money'] >= item['price']:
            await update_user_money(uid, -item['price'], f"شراء {rank_name}", None)
            await db.execute("INSERT INTO user_purchases (user_id, item_id) VALUES (?, ?) ON CONFLICT DO NOTHING", uid, item['id'])
            await message.reply(f"✅ تم شراء رتبة *{rank_name}* بنجاح!")
        else:
            await message.reply(f"❌ رصيدك غير كافٍ (تحتاج {item['price']} {CURRENCY_NAME})")

# ========== إضافة XP عند أي رسالة عادية ==========
async def add_xp_on_message(message: Message):
    await get_or_create_user(message.from_user)
    if not message.text or message.text.startswith(("#", "$")):
        return
    if message.from_user.id in ADMIN_IDS:
        return
    await add_xp(message.from_user.id, XP_PER_MESSAGE, message.chat.id, message.from_user.full_name)
    await update_user_stats(message.from_user.id, 'total_messages')

def register_event_handlers(dp: Dispatcher):
    dp.message.register(handle_admin_commands, lambda m: m.text and m.text.startswith("$"))
    dp.message.register(handle_member_commands, lambda m: m.text and m.text.startswith("#"))
    dp.message.register(add_xp_on_message)
