from aiogram import Dispatcher
from aiogram.types import Message
from config import ADMIN_IDS, CURRENCY_NAME
from _core.users import update_user_money, get_user
from _core.xp import add_xp, get_xp_progress
from _core.games import cmd_game
from _core.titles import set_user_title, remove_user_title
import re

# ------------------- أوامر الأدمن بالرد -------------------
async def handle_admin_reply_commands(message: Message):
    if not message.reply_to_message:
        return
    if message.from_user.id not in ADMIN_IDS:
        return
    
    admin = message.from_user
    target = message.reply_to_message.from_user
    text = message.text.strip()
    
    # كتم المستخدم (تغيير حالة المستخدم في قاعدة البيانات)
    if text.startswith("$كتم"):
        parts = text.split(maxsplit=2)
        if len(parts) >= 2:
            duration = parts[1]  # مثلاً 10m, 1h, 1d
            reason = parts[2] if len(parts) > 2 else "لا يوجد سبب"
            # تحويل المدة إلى دقائق (يمكنك تطويرها)
            await message.reply(f"🔇 تم كتم {target.full_name} لمدة {duration}. السبب: {reason}")
            # هنا يمكن تحديث حالة المستخدم في قاعدة البيانات
        else:
            await message.reply("❌ استخدم: $كتم 10m سبب الاختيار")
    
    # حظر المستخدم
    elif text.startswith("$حظر"):
        parts = text.split(maxsplit=1)
        reason = parts[1] if len(parts) > 1 else "لا يوجد سبب"
        await message.reply(f"🚫 تم حظر {target.full_name}. السبب: {reason}")
        # تحديث حالة المستخدم إلى banned
    
    # طرد المستخدم (يتطلب صلاحية البوت لطرد الأعضاء)
    elif text.startswith("$طرد"):
        reason = text[5:].strip() or "لا يوجد سبب"
        await message.reply(f"👢 تم طرد {target.full_name}. السبب: {reason}")
        # محاولة طرد العضو من المجموعة
        try:
            await message.chat.ban_member(target.id)
            await message.chat.unban_member(target.id)
        except:
            pass
    
    # خصم رصيد
    elif text.startswith("$خصم"):
        parts = text.split(maxsplit=2)
        if len(parts) >= 2 and parts[1].isdigit():
            amount = int(parts[1])
            reason = parts[2] if len(parts) > 2 else "خصم بواسطة أدمن"
            await update_user_money(target.id, -amount, reason, admin.id)
            await message.reply(f"✅ تم خصم {amount} {CURRENCY_NAME} من {target.full_name}\n📝 السبب: {reason}")
        else:
            await message.reply("❌ استخدم: $خصم 50 سبب مخالفة")
    
    # إعطاء رصيد (مكافأة)
    elif text.startswith("$اعطاء") or text.startswith("$إعطاء"):
        parts = text.split(maxsplit=2)
        if len(parts) >= 2 and parts[1].isdigit():
            amount = int(parts[1])
            reason = parts[2] if len(parts) > 2 else "مكافأة من الأدمن"
            await update_user_money(target.id, amount, reason, admin.id)
            await message.reply(f"✅ تم إضافة {amount} {CURRENCY_NAME} إلى {target.full_name}\n🎁 السبب: {reason}")
        else:
            await message.reply("❌ استخدم: $اعطاء 100 مكافأة نشاط")
    
    # تغيير اللقب
    elif text.startswith("$لقب"):
        new_title = text[5:].strip()
        if new_title:
            await set_user_title(target.id, new_title)
            await message.reply(f"🏷️ تم منح اللقب '{new_title}' إلى {target.full_name}")
        else:
            await message.reply("❌ استخدم: $لقب بطل")
    
    # سجل الأدمن (آخر 10 عمليات)
    elif text == "$سجل":
        from db import db
        rows = await db.fetch("SELECT * FROM economy_log WHERE admin_id = $1 ORDER BY timestamp DESC LIMIT 10", admin.id)
        if rows:
            log_text = "📜 *آخر عملياتك:*\n"
            for row in rows:
                log_text += f"• {row['amount']} {CURRENCY_NAME} للمستخدم {row['user_id']} - {row['reason']}\n"
            await message.reply(log_text, parse_mode="Markdown")
        else:
            await message.reply("📭 لا توجد عمليات مسجلة لك.")

# ------------------- أوامر الأعضاء (#) -------------------
async def handle_hashtag_commands(message: Message):
    text = message.text.strip()
    user_id = message.from_user.id
    
    # عرض الملف الشخصي
    if text in ["#ملفي", "#حسابي", "#معلوماتي", "#معلومات", "#ملف"]:
        user = await get_user(user_id)
        progress = await get_xp_progress(user_id)
        reply = f"""╭━━━━━━━━━━━━━━━╮
┃ 👤 *الملف الشخصي* 👤
╰━━━━━━━━━━━━━━━╯

✨ *الاسم:* {user['full_name']}
🆔 *المعرف:* @{user['username'] or 'لا يوجد'}

━━━━━━━━━━━━━━━
💰 *الرصيد:* {user['money']} {CURRENCY_NAME}
🏆 *اللقب:* {user['title'] or 'لا يوجد'}
⭐ *النقاط (XP):* {user['xp']}
📊 *المستوى:* {user['level']}

📈 *شريط التقدم:*
{progress['bar']} {progress['percent']}%

⏳ *المتبقي للمستوى التالي:* {progress['remaining']} XP

━━━━━━━━━━━━━━━
🎮 *نقاط الألعاب:* {user['game_points']}
🏅 *الفوز في الألعاب:* {user['wins']}
"""
        await message.reply(reply, parse_mode="Markdown")
    
    # عرض الرصيد فقط
    elif text in ["#فلوس", "#فلوسي", "#رصيدي"]:
        user = await get_user(user_id)
        await message.reply(f"💰 رصيدك الحالي: {user['money']} {CURRENCY_NAME}")
    
    # تشغيل لعبة
    elif text in ["#لعبة", "#العب", "#العاب"]:
        await cmd_game(message)
    
    # عرض المستوى فقط
    elif text in ["#مستواي", "#لـيفلي", "#نقاطي"]:
        user = await get_user(user_id)
        progress = await get_xp_progress(user_id)
        await message.reply(f"📊 *المستوى {user['level']}*\n{progress['bar']} {progress['percent']}%\n{progress['remaining']} XP للمستوى التالي", parse_mode="Markdown")

# ------------------- تسجيل المعالجات -------------------
def register_event_handlers(dp: Dispatcher):
    # أوامر الأدمن بالرد (تبدأ بـ $)
    dp.message.register(handle_admin_reply_commands, lambda msg: msg.text and msg.text.startswith("$"))
    # أوامر الأعضاء بعلامة #
    dp.message.register(handle_hashtag_commands, lambda msg: msg.text and msg.text.startswith("#"))
