from aiogram import Dispatcher
from aiogram.types import Message
from config import ADMIN_IDS, CURRENCY_NAME, XP_PER_MESSAGE
from _core.users import update_user_money, get_user, set_user_status, get_or_create_user, is_admin, is_general_mod, add_general_mod, remove_general_mod
from _core.xp import add_xp, get_xp_progress
from _core.games import start_game_with_choice
from _core.titles import set_user_title
from _core.notify import bot, send_auto_delete, send_admin_notification
from db import db
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

# ========== حذف رسالة الأمر بعد 3 ثوانٍ ==========
async def delete_command(msg: Message, delay=3):
    await asyncio.sleep(delay)
    try:
        await msg.delete()
    except:
        pass

# ========== أوامر الأدمن والمشرف العام ($) ==========
async def handle_admin_commands(message: Message):
    if not message.reply_to_message:
        return
    uid = message.from_user.id
    is_adm = await is_admin(uid)
    is_mod = await is_general_mod(uid)
    if not (is_adm or is_mod):
        return
    target = message.reply_to_message.from_user
    text = message.text.strip()
    chat_id = message.chat.id
    executor_name = message.from_user.full_name
    target_name = target.full_name

    # ---- الأدمن فقط ----
    if text.startswith("$رفع مشرف"):
        if not is_adm:
            await send_auto_delete(chat_id, "❌ للأدمن فقط")
            return
        await add_general_mod(target.id, uid)
        await send_auto_delete(chat_id, f"✅ تم رفع {target_name} مشرفاً عاماً")
        await send_admin_notification(chat_id, executor_name, target_name, "🛡️ رفع مشرف عام", "")
    elif text.startswith("$حذف مشرف"):
        if not is_adm:
            await send_auto_delete(chat_id, "❌ للأدمن فقط")
            return
        await remove_general_mod(target.id)
        await send_auto_delete(chat_id, f"✅ تم حذف صلاحيات المشرف عن {target_name}")
    elif text.startswith("$خصم"):
        if not is_adm:
            await send_auto_delete(chat_id, "❌ للأدمن فقط")
            return
        parts = text.split(maxsplit=2)
        if len(parts) >= 2 and parts[1].isdigit():
            amt = int(parts[1])
            reason = parts[2] if len(parts) > 2 else "خصم"
            await update_user_money(target.id, -amt, reason, uid)
            await send_auto_delete(chat_id, f"✅ خصم {amt} من {target_name}")
            await send_admin_notification(chat_id, executor_name, target_name, "💰 خصم رصيد", f"-{amt}\nالسبب: {reason}")
        else:
            await send_auto_delete(chat_id, "❌ استخدم: $خصم 50 سبب")
    elif text.startswith("$اعطاء") or text.startswith("$إعطاء"):
        if not is_adm:
            await send_auto_delete(chat_id, "❌ للأدمن فقط")
            return
        parts = text.split(maxsplit=2)
        if len(parts) >= 2 and parts[1].isdigit():
            amt = int(parts[1])
            reason = parts[2] if len(parts) > 2 else "مكافأة"
            await update_user_money(target.id, amt, reason, uid)
            await send_auto_delete(chat_id, f"✅ إضافة {amt} إلى {target_name}")
            await send_admin_notification(chat_id, executor_name, target_name, "💰 إضافة رصيد", f"+{amt}\nالسبب: {reason}")
        else:
            await send_auto_delete(chat_id, "❌ استخدم: $اعطاء 100 سبب")

    # ---- أوامر مشتركة ----
    elif text.startswith("$معلومات"):
        u = await get_user(target.id)
        if u:
            info = f"📄 {u['full_name']}\n💰 {u['money']}\n⭐ XP: {u['xp']}\n📊 مستوى {u['level']}\n🏷️ لقب: {u['title'] or 'لا يوجد'}"
            msg = await message.reply(info, parse_mode="Markdown")
            asyncio.create_task(delete_command(msg, 30))
            asyncio.create_task(delete_command(message, 1))
    elif text.startswith("$كتم"):
        parts = text.split(maxsplit=2)
        duration = parts[1] if len(parts) >= 2 else "30m"
        reason = parts[2] if len(parts) > 2 else "لا سبب"
        await set_user_status(target.id, "muted")
        await send_auto_delete(chat_id, f"🔇 كتم {target_name} لمدة {duration}")
        await send_admin_notification(chat_id, executor_name, target_name, "🔇 كتم", f"لمدة {duration}\nالسبب: {reason}")
    elif text == "$فك كتم":
        await set_user_status(target.id, "active")
        await send_auto_delete(chat_id, f"🔈 فك كتم {target_name}")
        await send_admin_notification(chat_id, executor_name, target_name, "🔈 فك كتم", "")
    elif text.startswith("$حظر"):
        reason = text[5:].strip() or "لا سبب"
        await set_user_status(target.id, "banned")
        await send_auto_delete(chat_id, f"🚫 حظر {target_name}")
        await send_admin_notification(chat_id, executor_name, target_name, "🚫 حظر", reason)
    elif text == "$فك حظر":
        await set_user_status(target.id, "active")
        await send_auto_delete(chat_id, f"✅ فك حظر {target_name}")
        await send_admin_notification(chat_id, executor_name, target_name, "✅ فك حظر", "")
    elif text.startswith("$طرد"):
        reason = text[5:].strip() or "لا سبب"
        await send_auto_delete(chat_id, f"👢 طرد {target_name}")
        await send_admin_notification(chat_id, executor_name, target_name, "🗑️ طرد", reason)
        try:
            await message.chat.ban_member(target.id)
            await message.chat.unban_member(target.id)
        except: pass
    elif text.startswith("$لقب"):
        new_title = text[5:].strip()
        if new_title:
            await set_user_title(target.id, new_title)
            await send_auto_delete(chat_id, f"🏷️ لقب {target_name} ← {new_title}")
            await send_admin_notification(chat_id, executor_name, target_name, "🏷️ تغيير لقب", new_title)
        else:
            await send_auto_delete(chat_id, "❌ استخدم: $لقب بطل")
    elif text == "$سجل":
        rows = await db.fetch("SELECT amount, reason FROM economy_log WHERE admin_id = ? ORDER BY timestamp DESC LIMIT 10", uid)
        if rows:
            log = "📜 سجلك:\n" + "\n".join([f"{r['amount']} - {r['reason']}" for r in rows])
            msg = await message.reply(log, parse_mode="Markdown")
            asyncio.create_task(delete_command(msg, 30))

# ========== أوامر الأعضاء (#) ==========
async def handle_member_commands(message: Message):
    text = message.text.strip()
    uid = message.from_user.id
    await get_or_create_user(message.from_user)
    asyncio.create_task(delete_command(message, 3))

    if text in ["#ملفي", "#حسابي", "#معلوماتي"]:
        user = await get_user(uid)
        stats = await get_user_stats(uid)
        progress = await get_xp_progress(uid)
        reply = f"""╭━━━━━━━━━━━━━━━━━━━━━━╮
┃ 👤 *الملف الشخصي* 👤
╰━━━━━━━━━━━━━━━━━━━━━━╯

✨ *الاسم:* {user['full_name']}
🆔 *المعرف:* @{user['username'] or 'لا يوجد'}

💰 *الرصيد:* {user['money']} {CURRENCY_NAME}
⭐ *XP:* {user['xp']}
📊 *المستوى:* {user['level']}
🏷️ *اللقب:* {user['title'] or 'لا يوجد'}

📨 *الرسائل:* {stats['total_messages']}
⚠️ *التحذيرات:* {stats['total_warns']}
📈 {progress['bar']} {progress['percent']}%"""
        msg = await message.reply(reply, parse_mode="Markdown")
        asyncio.create_task(delete_command(msg, 30))
    elif text in ["#فلوس", "#فلوسي"]:
        user = await get_user(uid)
        msg = await message.reply(f"💰 رصيدك: {user['money']} {CURRENCY_NAME}")
        asyncio.create_task(delete_command(msg, 30))
    elif text in ["#لقب", "#لقبي"]:
        user = await get_user(uid)
        msg = await message.reply(f"🏷️ لقبك: {user['title'] or 'لا يوجد'}")
        asyncio.create_task(delete_command(msg, 30))
    elif text in ["#لعبة", "#العب", "#العاب"]:
        # عرض قائمة الألعاب برسالة في المجموعة تختفي بعد 15 ثانية
        menu = """🎮 *قائمة الألعاب*
1️⃣ لغز
2️⃣ سؤال عام
3️⃣ اختيار من متعدد
4️⃣ سرعة (معكوس كلمة)
5️⃣ مثل شعبي
6️⃣ حظ (صندوق)
━━━━━━━━━━━━━
📝 *أرسل رقم اللعبة (1-6)*"""
        msg = await message.reply(menu, parse_mode="Markdown")
        asyncio.create_task(delete_command(msg, 15))
        # حفظ اختيار المستخدم مؤقتاً (سنستخدم متغير مؤقت بسيط، لكن الأفضل تخزين الحالة)
        # سنقوم بإضافة معالج لاستقبال الأرقام في نفس الدالة عبر تعليق
        # لكننا سنضيف معالج أرقام منفصل.
    elif text in ["#سوق", "#محل"]:
        items = await db.fetch("SELECT name, price FROM shop_items ORDER BY rank_level")
        if not items:
            await send_auto_delete(message.chat.id, "🏪 السوق فارغ")
            return
        txt = "🏪 *السوق*\n"
        for it in items:
            txt += f"• {it['name']} - 💰{it['price']}\n"
        txt += "\nللشراء: `#شراء <اسم الرتبة>`"
        msg = await message.reply(txt, parse_mode="Markdown")
        asyncio.create_task(delete_command(msg, 30))
    elif text.startswith("#شراء"):
        parts = text.split(maxsplit=1)
        if len(parts) < 2:
            await send_auto_delete(message.chat.id, "❌ استخدم: #شراء اسم الرتبة")
            return
        rank = parts[1]
        item = await db.fetchrow("SELECT * FROM shop_items WHERE name = ?", rank)
        if not item:
            await send_auto_delete(message.chat.id, "❌ الرتبة غير موجودة")
            return
        user = await get_user(uid)
        if user['money'] >= item['price']:
            await update_user_money(uid, -item['price'], f"شراء {rank}", None)
            await db.execute("INSERT INTO user_purchases (user_id, item_id) VALUES (?, ?) ON CONFLICT DO NOTHING", uid, item['id'])
            await send_auto_delete(message.chat.id, f"✅ تم شراء رتبة *{rank}* بنجاح!")
        else:
            await send_auto_delete(message.chat.id, f"❌ رصيدك غير كافٍ (تحتاج {item['price']})")
    elif text in ["#مستواي", "#نقاطي"]:
        progress = await get_xp_progress(uid)
        msg = await message.reply(f"📊 المستوى {progress['level']}\n{progress['bar']} {progress['percent']}%")
        asyncio.create_task(delete_command(msg, 30))

# ========== معالج اختيار اللعبة برقم ==========
async def handle_game_choice(message: Message):
    if not message.text or not message.text.isdigit():
        return
    choice = int(message.text)
    if 1 <= choice <= 6:
        game_map = {1: "puzzles", 2: "general_qa", 3: "mcq", 4: "speed_words", 5: "proverbs", 6: "luck_boxes"}
        game_type = game_map[choice]
        await start_game_with_choice(message, game_type)
        # حذف رسالة الاختيار
        asyncio.create_task(delete_command(message, 1))

# ========== إضافة XP تلقائياً ==========
async def add_xp_on_message(message: Message):
    await get_or_create_user(message.from_user)
    if not message.text or message.text.startswith(("#", "$")):
        return
    if await is_admin(message.from_user.id):
        return
    await add_xp(message.from_user.id, XP_PER_MESSAGE, message.chat.id, message.from_user.full_name)
    await update_user_stats(message.from_user.id, 'total_messages')

def register_event_handlers(dp: Dispatcher):
    dp.message.register(handle_admin_commands, lambda m: m.text and m.text.startswith("$"))
    dp.message.register(handle_member_commands, lambda m: m.text and m.text.startswith("#"))
    dp.message.register(handle_game_choice, lambda m: m.text and m.text.isdigit())
    dp.message.register(add_xp_on_message)
