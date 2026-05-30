from aiogram import Dispatcher
from aiogram.types import Message, ChatPermissions
from config import ADMIN_IDS, CURRENCY_NAME, XP_PER_MESSAGE
from _core.users import update_user_money, get_user, set_user_status, get_or_create_user, is_admin, is_general_mod, add_general_mod, remove_general_mod
from _core.xp import add_xp, get_xp_progress
from _core.games import start_game_with_choice
from _core.titles import set_user_title
from _core.notify import send_auto_delete, send_admin_notification
from db import db
import asyncio

async def delete_after(msg, seconds):
    await asyncio.sleep(seconds)
    try: await msg.delete()
    except: pass

# أوامر $ (نفس السابق لكن بدون تغيير)
async def dollar_commands(message: Message):
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
    admin_name = message.from_user.full_name
    target_name = target.full_name

    if text.startswith("$خصم") and is_adm:
        parts = text.split(maxsplit=2)
        if len(parts) >= 2 and parts[1].isdigit():
            amt = int(parts[1])
            reason = parts[2] if len(parts) > 2 else "خصم"
            await update_user_money(target.id, -amt, reason, uid)
            await send_auto_delete(chat_id, f"✅ خصم {amt} {CURRENCY_NAME} من {target_name}\nالسبب: {reason}")
            await send_admin_notification(admin_name, target_name, "💰 خصم رصيد", f"-{amt}")
        else:
            await send_auto_delete(chat_id, "❌ استخدم: $خصم 50 سبب")
    elif text.startswith("$اعطاء") and is_adm:
        parts = text.split(maxsplit=2)
        if len(parts) >= 2 and parts[1].isdigit():
            amt = int(parts[1])
            reason = parts[2] if len(parts) > 2 else "مكافأة"
            await update_user_money(target.id, amt, reason, uid)
            await send_auto_delete(chat_id, f"✅ إضافة {amt} {CURRENCY_NAME} إلى {target_name}\nالسبب: {reason}")
            await send_admin_notification(admin_name, target_name, "💰 إضافة رصيد", f"+{amt}")
        else:
            await send_auto_delete(chat_id, "❌ استخدم: $اعطاء 100 سبب")
    elif text.startswith("$كتم"):
        duration = text.split()[1] if len(text.split()) > 1 else "30m"
        await set_user_status(target.id, "muted")
        try:
            await message.chat.restrict_member(target.id, permissions=ChatPermissions(can_send_messages=False))
            await send_auto_delete(chat_id, f"🔇 تم كتم {target_name} لمدة {duration}")
        except:
            await send_auto_delete(chat_id, f"⚠️ لا يمكن كتم {target_name} (صلاحيات)")
        await send_admin_notification(admin_name, target_name, "🔇 كتم", f"لمدة {duration}")
    elif text == "$فك كتم":
        await set_user_status(target.id, "active")
        try:
            await message.chat.restrict_member(target.id, permissions=ChatPermissions(can_send_messages=True, can_send_media_messages=True, can_send_other_messages=True))
            await send_auto_delete(chat_id, f"🔈 تم فك كتم {target_name}")
        except:
            await send_auto_delete(chat_id, f"⚠️ لا يمكن فك الكتم")
        await send_admin_notification(admin_name, target_name, "🔈 فك كتم", "")
    elif text.startswith("$حظر"):
        await set_user_status(target.id, "banned")
        try:
            await message.chat.ban_member(target.id)
            await send_auto_delete(chat_id, f"🚫 تم حظر {target_name}")
        except:
            await send_auto_delete(chat_id, f"⚠️ لا يمكن حظر {target_name}")
        await send_admin_notification(admin_name, target_name, "🚫 حظر", "")
    elif text == "$فك حظر":
        await set_user_status(target.id, "active")
        try:
            await message.chat.unban_member(target.id)
            await send_auto_delete(chat_id, f"✅ تم فك حظر {target_name}")
        except:
            await send_auto_delete(chat_id, f"⚠️ لا يمكن فك الحظر")
        await send_admin_notification(admin_name, target_name, "✅ فك حظر", "")
    elif text.startswith("$طرد"):
        await send_auto_delete(chat_id, f"👢 تم طرد {target_name}")
        await send_admin_notification(admin_name, target_name, "🗑️ طرد", "")
        try:
            await message.chat.ban_member(target.id)
            await message.chat.unban_member(target.id)
        except: pass
    elif text.startswith("$لقب") and is_adm:
        new_title = text[5:].strip()
        if new_title:
            await set_user_title(target.id, new_title)
            await send_auto_delete(chat_id, f"🏷️ لقب {target_name} ← {new_title}")
            await send_admin_notification(admin_name, target_name, "🏷️ تغيير لقب", new_title)
    elif text.startswith("$معلومات"):
        u = await get_user(target.id)
        if u:
            msg = await message.reply(f"📄 {u['full_name']}\n💰 {u['money']}\n⭐ {u['xp']}\n📊 مستوى {u['level']}\n🏷️ لقب: {u['title'] or 'لا يوجد'}")
            asyncio.create_task(delete_after(msg, 30))
    elif text == "$سجل" and is_adm:
        rows = await db.fetch("SELECT amount, reason, user_id FROM economy_log WHERE admin_id = ? ORDER BY timestamp DESC LIMIT 10", uid)
        if rows:
            log = "📜 سجلك:\n"
            for r in rows:
                log += f"• {r['amount']} {CURRENCY_NAME} للمستخدم {r['user_id']} - {r['reason']}\n"
            msg = await message.reply(log)
            asyncio.create_task(delete_after(msg, 30))
    elif text.startswith("$تحذير") and is_adm:
        reason = text[8:].strip() or "لا يوجد سبب"
        user = await get_user(target.id)
        warnings = user['warnings'] + 1
        await db.execute("UPDATE users SET warnings = ? WHERE telegram_id = ?", warnings, target.id)
        await send_auto_delete(chat_id, f"⚠️ تم تحذير {target_name} (التحذير {warnings}/3)\nالسبب: {reason}")
        await send_admin_notification(admin_name, target_name, "⚠️ تحذير", f"التحذير {warnings}/3\nالسبب: {reason}")
        if warnings >= 3:
            await set_user_status(target.id, "banned")
            await send_auto_delete(chat_id, f"🚫 تم حظر {target_name} تلقائياً لـ 3 تحذيرات")

# ========== أوامر الأعضاء ==========
async def handle_member_commands(message: Message):
    text = message.text.strip()
    uid = message.from_user.id
    await get_or_create_user(message.from_user)
    asyncio.create_task(delete_after(message, 3))

    if text in ["#ملفي", "#حسابي", "#معلوماتي"]:
        user = await get_user(uid)
        progress = await get_xp_progress(uid)
        last_action = await db.fetchrow("SELECT amount, reason, admin_id FROM economy_log WHERE user_id = ? ORDER BY timestamp DESC LIMIT 1", uid)
        last_action_text = "لا يوجد"
        if last_action:
            admin = await get_user(last_action['admin_id']) if last_action['admin_id'] else None
            admin_name = admin['full_name'] if admin else "نظام"
            last_action_text = f"⬅️ {admin_name} | {last_action['reason']} | {last_action['amount']} {CURRENCY_NAME}"
        # استخدام نص عادي بدلاً من Markdown لتجنب الأخطاء
        reply = f"""╭━━━━━━━━━━━━━━━━━━━━━━╮
┃ 👤 الملف الشخصي
╰━━━━━━━━━━━━━━━━━━━━━━╯

✨ الاسم: {user['full_name']}
🆔 المعرف: @{user['username'] or 'لا يوجد'}

⬅️ 💲 فلوسك: {user['money']} {CURRENCY_NAME}
⬅️ 💎 نقاطك (XP): {user['xp']}
⬅️ 🪪 عضويتك: {user['title'] or 'عادي'}
⬅️ 💠 المستوى: {user['level']}
⬅️ ❗️ التحذيرات: {user['warnings']}/3

📈 {progress['bar']} {progress['percent']}%

📌 آخر إجراء:
{last_action_text}
━━━━━━━━━━━━━━━━━━━━━━"""
        msg = await message.reply(reply)  # لا يوجد parse_mode
        asyncio.create_task(delete_after(msg, 30))
    elif text in ["#فلوس", "#فلوسي"]:
        user = await get_user(uid)
        msg = await message.reply(f"⬅️ 💲 فلوسك: {user['money']} {CURRENCY_NAME}")
        asyncio.create_task(delete_after(msg, 30))
    elif text in ["#لعبة", "#العب", "#العاب"]:
        menu = """🎮 قائمة الألعاب
1 🧠 لغز
2 ❓ سؤال عام
3 🔘 اختيار من متعدد
4 ⚡ سرعة (معكوس كلمة)
5 📜 مثل شعبي
6 🎲 حظ (صندوق)
━━━━━━━━━━━━━
📝 أرسل رقم اللعبة (1-6)"""
        msg = await message.reply(menu)
        asyncio.create_task(delete_after(msg, 30))
    elif text.isdigit() and 1 <= int(text) <= 6:
        game_map = {1:"puzzles",2:"general_qa",3:"mcq",4:"speed_words",5:"proverbs",6:"luck_boxes"}
        await start_game_with_choice(message, game_map[int(text)])
        await delete_after(message, 1)
    elif text in ["#سوق", "#محل"]:
        items = await db.fetch("SELECT name, price FROM shop_items ORDER BY rank_level")
        if not items:
            await send_auto_delete(message.chat.id, "🏪 السوق فارغ")
            return
        txt = "🏪 السوق\n"
        for it in items:
            txt += f"• {it['name']} - 💰{it['price']}\n"
        txt += "\nللشراء: #شراء <اسم الرتبة>"
        msg = await message.reply(txt)
        asyncio.create_task(delete_after(msg, 30))
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
        asyncio.create_task(delete_after(msg, 30))

async def add_xp_handler(message: Message):
    await get_or_create_user(message.from_user)
    if message.text and not message.text.startswith(("#", "$")):
        await add_xp(message.from_user.id, XP_PER_MESSAGE, message.chat.id, message.from_user.full_name)

def register_event_handlers(dp: Dispatcher):
    dp.message.register(dollar_commands, lambda m: m.text and m.text.startswith("$"))
    dp.message.register(handle_member_commands, lambda m: m.text and m.text.startswith("#"))
    dp.message.register(add_xp_handler)
