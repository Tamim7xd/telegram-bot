from aiogram import Dispatcher
from aiogram.types import Message, ChatPermissions
from config import ADMIN_IDS, CURRENCY_NAME, XP_PER_MESSAGE, GROUP_ID
from _core.users import update_user_money, get_user, set_user_status, get_or_create_user, is_admin, is_general_mod, is_admin_mod, add_general_mod, remove_general_mod, add_admin_mod, remove_admin_mod, add_warning, get_user_warnings_count, get_user_warnings_list, reset_warnings
from _core.xp import add_xp, get_xp_progress, increment_message_count
from _core.games import start_game_with_choice
from _core.titles import set_user_title
from _core.notify import send_auto_delete, send_admin_notification
from db import db
import asyncio

def format_number(num):
    return f"{num:,}".replace(",", " ").replace(",", ".")

async def delete_after(msg, seconds):
    await asyncio.sleep(seconds)
    try: await msg.delete()
    except: pass

# ========== أوامر $ ==========
async def dollar_commands(message: Message):
    if not message.reply_to_message:
        return
    uid = message.from_user.id
    is_adm = await is_admin(uid)
    is_gen_mod = await is_general_mod(uid)
    is_adm_mod = await is_admin_mod(uid)
    if not (is_adm or is_gen_mod or is_adm_mod):
        return
    target = message.reply_to_message.from_user
    text = message.text.strip()
    chat_id = message.chat.id
    admin_name = message.from_user.full_name
    target_name = target.full_name

    if text.startswith("$خصم") and (is_adm or is_adm_mod):
        parts = text.split(maxsplit=2)
        if len(parts) >= 2 and parts[1].isdigit():
            amt = int(parts[1])
            reason = parts[2] if len(parts) > 2 else "خصم"
            await update_user_money(target.id, -amt, reason, uid)
            await send_auto_delete(chat_id, f"✅ خصم {format_number(amt)} {CURRENCY_NAME} من {target_name}\nالسبب: {reason}")
            await send_admin_notification(admin_name, target_name, "💰 خصم رصيد", f"-{format_number(amt)}")
        else:
            await send_auto_delete(chat_id, "❌ استخدم: $خصم 50 سبب")
    elif text.startswith("$مكافئة") and (is_adm or is_adm_mod):
        parts = text.split(maxsplit=2)
        if len(parts) >= 2 and parts[1].isdigit():
            amt = int(parts[1])
            reason = parts[2] if len(parts) > 2 else "مكافأة"
            await update_user_money(target.id, amt, reason, uid)
            await send_auto_delete(chat_id, f"✅ إضافة {format_number(amt)} {CURRENCY_NAME} إلى {target_name}\nالسبب: {reason}")
            await send_admin_notification(admin_name, target_name, "💰 إضافة رصيد", f"+{format_number(amt)}")
        else:
            await send_auto_delete(chat_id, "❌ استخدم: $مكافئة 100 سبب")
    elif text.startswith("$تحذير") and (is_adm or is_gen_mod or is_adm_mod):
        reason = text[8:].strip() or "لا يوجد سبب"
        new_count = await add_warning(target.id, reason, uid)
        await send_auto_delete(chat_id, f"⚠️ تم تحذير {target_name} (التحذير {new_count}/100)\nالسبب: {reason}")
        await send_admin_notification(admin_name, target_name, "⚠️ تحذير", f"التحذير {new_count}/100\nالسبب: {reason}")
    elif text.startswith("$معلومات") and (is_adm or is_gen_mod or is_adm_mod):
        u = await get_user(target.id)
        if u:
            msg = await message.reply(f"📄 {u['full_name']}\n💰 {format_number(u['money'])} {CURRENCY_NAME}\n⭐ XP: {u['xp']}\n📊 المستوى: {u['level']}\n🏷️ اللقب: {u['title'] or 'لا يوجد'}\n⚠️ التحذيرات: {u['warnings']}/100")
            asyncio.create_task(delete_after(msg, 30))
    elif text.startswith("$فلوس") and (is_adm or is_gen_mod or is_adm_mod):
        u = await get_user(target.id)
        if u:
            msg = await message.reply(f"💰 فلوس {target_name}: {format_number(u['money'])} {CURRENCY_NAME}")
            asyncio.create_task(delete_after(msg, 30))
    elif text.startswith("$التحذيرات") and (is_adm or is_gen_mod or is_adm_mod):
        warns = await get_user_warnings_list(target.id, 5)
        if warns:
            txt = f"⚠️ تحذيرات {target_name}:\n"
            for w in warns:
                admin = await get_user(w['admin_id'])
                admin_name = admin['full_name'] if admin else "نظام"
                txt += f"• {w['reason']} (بواسطة {admin_name}) - {w['created_at']}\n"
            msg = await message.reply(txt)
            asyncio.create_task(delete_after(msg, 30))
        else:
            await send_auto_delete(chat_id, f"✅ {target_name} ليس لديه تحذيرات")
    elif text == "$سجل" and (is_adm or is_adm_mod):
        rows = await db.fetch("SELECT amount, reason, user_id FROM economy_log WHERE admin_id = ? ORDER BY timestamp DESC LIMIT 10", uid)
        if rows:
            log = "📜 سجلك:\n"
            for r in rows:
                log += f"• {format_number(r['amount'])} {CURRENCY_NAME} للمستخدم {r['user_id']} - {r['reason']}\n"
            msg = await message.reply(log)
            asyncio.create_task(delete_after(msg, 30))
        else:
            await send_auto_delete(chat_id, "📭 لا توجد عمليات مسجلة لك")

# ========== أوامر الأعضاء (#) ==========
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
            last_action_text = f"{admin_name} | {last_action['reason']} | {format_number(last_action['amount'])} {CURRENCY_NAME}"
        reply = f"""╭━━━━━━━━━━━━━━━━━━━━━━╮
┃ 👤 الملف الشخصي
╰━━━━━━━━━━━━━━━━━━━━━━╯

✨ الاسم: {user['full_name']}
🆔 المعرف: @{user['username'] or 'لا يوجد'}

⬅️ 💲 فلوسك: {format_number(user['money'])} {CURRENCY_NAME}
⬅️ 💎 نقاطك (XP): {user['xp']}
⬅️ 🪪 عضويتك: {user['title'] or 'عادي'}
⬅️ 💠 المستوى: {user['level']}
⬅️ ❗️ التحذيرات: {user['warnings']}/100

📈 {progress['bar']} {progress['percent']}%

📌 آخر إجراء:
{last_action_text}
━━━━━━━━━━━━━━━━━━━━━━"""
        msg = await message.reply(reply)
        asyncio.create_task(delete_after(msg, 30))
    elif text in ["#فلوس", "#فلوسي"]:
        user = await get_user(uid)
        msg = await message.reply(f"⬅️ 💲 فلوسك: {format_number(user['money'])} {CURRENCY_NAME}")
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
    elif text in ["#مستواي", "#نقاطي"]:
        progress = await get_xp_progress(uid)
        msg = await message.reply(f"📊 المستوى {progress['level']}\n{progress['bar']} {progress['percent']}%")
        asyncio.create_task(delete_after(msg, 30))
    elif text in ["#سوق", "#محل"]:
        items = await db.fetch("SELECT id, name, price, rank_level FROM shop_items ORDER BY rank_level")
        if not items:
            await send_auto_delete(message.chat.id, "🏪 السوق فارغ")
            return
        txt = "🏪 السوق\n"
        for it in items:
            txt += f"🆔 {it['id']} - {it['name']} - 💰{format_number(it['price'])} - مستوى {it['rank_level']}\n"
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
            await send_admin_notification("نظام", user['full_name'], "شراء رتبة", f"{rank} - {format_number(item['price'])}")
        else:
            await send_auto_delete(message.chat.id, f"❌ رصيدك غير كافٍ (تحتاج {format_number(item['price'])} {CURRENCY_NAME})")

# ========== إضافة XP ومكافأة 100 رسالة ==========
async def add_xp_handler(message: Message):
    await get_or_create_user(message.from_user)
    if not message.text or message.text.startswith(("#", "$")):
        return
    if await is_admin(message.from_user.id):
        return
    await add_xp(message.from_user.id, XP_PER_MESSAGE, message.chat.id, message.from_user.full_name)
    rewarded = await increment_message_count(message.from_user.id)
    if rewarded:
        await send_auto_delete(message.chat.id, f"🎉 مبروك! {message.from_user.full_name}\nلقد وصلت إلى 100 رسالة!\n💰 +5,000 {CURRENCY_NAME}")

def register_event_handlers(dp: Dispatcher):
    dp.message.register(dollar_commands, lambda m: m.text and m.text.startswith("$"))
    dp.message.register(handle_member_commands, lambda m: m.text and m.text.startswith("#"))
    dp.message.register(add_xp_handler)
