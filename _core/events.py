from aiogram import Dispatcher
from aiogram.types import Message
from config import ADMIN_IDS, CURRENCY_NAME, XP_PER_MESSAGE
from _core.users import update_user_money, get_user, set_user_status, get_or_create_user, is_admin, is_general_mod
from _core.xp import add_xp, get_xp_progress
from _core.games import start_game_with_choice
from _core.titles import set_user_title
from _core.notify import send_auto_delete, send_admin_notification
from db import db
import asyncio

# حذف الرسائل بعد فترة
async def delete_after(msg, seconds):
    await asyncio.sleep(seconds)
    try: await msg.delete()
    except: pass

# أوامر $ (للأدمن والمشرف)
async def dollar_commands(message: Message):
    if not message.reply_to_message: return
    uid = message.from_user.id
    if not (await is_admin(uid) or await is_general_mod(uid)): return
    target = message.reply_to_message.from_user
    text = message.text.strip()
    chat_id = message.chat.id
    admin_name = message.from_user.full_name
    target_name = target.full_name

    # خصم
    if text.startswith("$خصم") and await is_admin(uid):
        parts = text.split()
        if len(parts)>=2 and parts[1].isdigit():
            amt = int(parts[1])
            reason = " ".join(parts[2:]) or "خصم"
            await update_user_money(target.id, -amt, reason, uid)
            await send_auto_delete(chat_id, f"✅ خصم {amt} من {target_name}\nالسبب: {reason}")
            await send_admin_notification(admin_name, target_name, "خصم رصيد", f"-{amt}")
        else:
            await send_auto_delete(chat_id, "❌ استخدم: $خصم 50 سبب")
    # إضافة
    elif text.startswith("$اعطاء") and await is_admin(uid):
        parts = text.split()
        if len(parts)>=2 and parts[1].isdigit():
            amt = int(parts[1])
            reason = " ".join(parts[2:]) or "مكافأة"
            await update_user_money(target.id, amt, reason, uid)
            await send_auto_delete(chat_id, f"✅ إضافة {amt} إلى {target_name}\nالسبب: {reason}")
            await send_admin_notification(admin_name, target_name, "إضافة رصيد", f"+{amt}")
        else:
            await send_auto_delete(chat_id, "❌ استخدم: $اعطاء 100 سبب")
    # كتم
    elif text.startswith("$كتم"):
        await set_user_status(target.id, "muted")
        await send_auto_delete(chat_id, f"🔇 تم كتم {target_name}")
        await send_admin_notification(admin_name, target_name, "كتم", "")
    # فك كتم
    elif text == "$فك كتم":
        await set_user_status(target.id, "active")
        await send_auto_delete(chat_id, f"🔈 تم فك كتم {target_name}")
        await send_admin_notification(admin_name, target_name, "فك كتم", "")
    # حظر
    elif text.startswith("$حظر"):
        await set_user_status(target.id, "banned")
        await send_auto_delete(chat_id, f"🚫 تم حظر {target_name}")
        await send_admin_notification(admin_name, target_name, "حظر", "")
    # فك حظر
    elif text == "$فك حظر":
        await set_user_status(target.id, "active")
        await send_auto_delete(chat_id, f"✅ فك حظر {target_name}")
        await send_admin_notification(admin_name, target_name, "فك حظر", "")
    # طرد
    elif text.startswith("$طرد"):
        await send_auto_delete(chat_id, f"👢 تم طرد {target_name}")
        await send_admin_notification(admin_name, target_name, "طرد", "")
        try:
            await message.chat.ban_member(target.id)
            await message.chat.unban_member(target.id)
        except: pass
    # لقب
    elif text.startswith("$لقب") and await is_admin(uid):
        new_title = text[5:].strip()
        if new_title:
            await set_user_title(target.id, new_title)
            await send_auto_delete(chat_id, f"🏷️ لقب {target_name} ← {new_title}")
            await send_admin_notification(admin_name, target_name, "تغيير لقب", new_title)
    # معلومات
    elif text.startswith("$معلومات"):
        u = await get_user(target.id)
        if u:
            msg = await message.reply(f"📄 {u['full_name']}\n💰 {u['money']}\n⭐ {u['xp']}\n📊 مستوى {u['level']}")
            asyncio.create_task(delete_after(msg, 30))
    # سجل
    elif text == "$سجل" and await is_admin(uid):
        rows = await db.fetch("SELECT amount, reason FROM economy_log WHERE admin_id = ? ORDER BY timestamp DESC LIMIT 10", uid)
        if rows:
            log = "📜 سجلك:\n" + "\n".join([f"{r['amount']} - {r['reason']}" for r in rows])
            msg = await message.reply(log)
            asyncio.create_task(delete_after(msg, 30))

# أوامر # (للأعضاء) - هذه هي الدالة التي يحتاجها bot_core.py
async def handle_member_commands(message: Message):
    text = message.text.strip()
    uid = message.from_user.id
    await get_or_create_user(message.from_user)
    asyncio.create_task(delete_after(message, 3))

    if text in ["#ملفي", "#حسابي"]:
        u = await get_user(uid)
        await message.reply(f"👤 {u['full_name']}\n💰 {u['money']}\n⭐ {u['xp']}\n📊 مستوى {u['level']}\n🏷️ لقب: {u['title'] or 'لا يوجد'}")
    elif text in ["#فلوس", "#فلوسي"]:
        u = await get_user(uid)
        await message.reply(f"💰 رصيدك: {u['money']}")
    elif text in ["#لعبة", "#العب", "#العاب"]:
        menu = """🎮 *قائمة الألعاب*
1 لغز
2 سؤال عام
3 اختيار من متعدد
4 سرعة
5 مثل شعبي
6 حظ
أرسل الرقم (1-6)"""
        msg = await message.reply(menu, parse_mode="Markdown")
        asyncio.create_task(delete_after(msg, 30))
    elif text.isdigit() and 1 <= int(text) <= 6:
        game_map = {1:"puzzles",2:"general_qa",3:"mcq",4:"speed_words",5:"proverbs",6:"luck_boxes"}
        await start_game_with_choice(message, game_map[int(text)])
        await delete_after(message, 1)

# إضافة XP لكل رسالة عادية
async def add_xp_handler(message: Message):
    await get_or_create_user(message.from_user)
    if message.text and not message.text.startswith(("#","$")):
        await add_xp(message.from_user.id, XP_PER_MESSAGE, message.chat.id, message.from_user.full_name)

def register_event_handlers(dp: Dispatcher):
    dp.message.register(dollar_commands, lambda m: m.text and m.text.startswith("$"))
    dp.message.register(handle_member_commands, lambda m: m.text and m.text.startswith("#"))
    dp.message.register(add_xp_handler)
