from aiogram import Dispatcher
from aiogram.types import Message
from config import ADMIN_IDS, CURRENCY_NAME, XP_PER_MESSAGE
from _core.users import update_user_money, get_user, set_user_status
from _core.xp import add_xp, get_xp_progress
from _core.games import cmd_game
from _core.titles import set_user_title
from _core.notify import bot
from db import db
from datetime import datetime, timedelta

# ========== دوال إحصائيات المستخدم ==========
async def get_user_stats(user_id: int):
    row = await db.fetchrow("SELECT * FROM user_stats WHERE user_id = $1", user_id)
    if not row:
        await db.execute("INSERT INTO user_stats (user_id) VALUES ($1) ON CONFLICT DO NOTHING", user_id)
        row = await db.fetchrow("SELECT * FROM user_stats WHERE user_id = $1", user_id)
    return dict(row)

async def update_user_stats(user_id: int, field: str, value=1, extra=None):
    if field in ["total_messages", "total_warns", "total_mutes", "total_bans", "total_kicks", "total_deductions"]:
        await db.execute(f"UPDATE user_stats SET {field} = {field} + $1 WHERE user_id = $2", value, user_id)
    elif field == "last_deduction" and extra:
        amount, reason = extra
        await db.execute("UPDATE user_stats SET last_deduction_amount = $1, last_deduction_reason = $2, last_deduction_at = NOW() WHERE user_id = $3", amount, reason, user_id)

# ========== إشعار متطور ==========
async def send_advanced_notification(chat_id: int, executor_name: str, executor_role: str, target_name: str, action: str, detail: str = "", duration: str = ""):
    border = "╭━━━━━━━━━━━━━━━━━━━━━━━━━━╮"
    text = f"""{border}
┃ 🔔 *إشـارة إداريـة* 🔔
╰━━━━━━━━━━━━━━━━━━━━━━━━━━╯

👤 *المنفذ:* {executor_name} ({executor_role})
👥 *المستخدم:* {target_name}
⚙️ *الإجراء:* {action}
📝 *التفاصيل:* {detail}
{f'⏱️ *المدة:* {duration}' if duration else ''}
🕒 *الوقت:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
━━━━━━━━━━━━━━━━━━━━━━━━━━"""
    await bot.send_message(chat_id, text, parse_mode="Markdown")

# ========== التحقق من المشرف ==========
async def is_mod(user_id: int) -> bool:
    row = await db.fetchrow("SELECT 1 FROM mods WHERE user_id = $1", user_id)
    return row is not None

# ========== أوامر الأدمن والمشرفين ($) ==========
async def handle_admin_commands(message: Message):
    if not message.reply_to_message:
        return
    user_id = message.from_user.id
    is_admin = user_id in ADMIN_IDS
    is_moderator = await is_mod(user_id)
    if not (is_admin or is_moderator):
        return
    target = message.reply_to_message.from_user
    text = message.text.strip()
    chat_id = message.chat.id
    executor_name = message.from_user.full_name
    target_name = target.full_name
    executor_role = "👑 أدمن" if is_admin else "🛡️ مشرف"

    # أوامر مشتركة
    if text.startswith("$معلومات"):
        user_data = await get_user(target.id)
        stats = await get_user_stats(target.id)
        info = f"📄 *معلومات {target_name}*\n💰 الرصيد: {user_data['money']}\n⭐ XP: {user_data['xp']}\n📊 المستوى: {user_data['level']}\n🏷️ اللقب: {user_data['title'] or 'لا يوجد'}\n📨 الرسائل: {stats.get('total_messages',0)}\n⚠️ التحذيرات: {stats.get('total_warns',0)}\n🔇 عدد الكتم: {stats.get('total_mutes',0)}\n🚫 عدد الحظر: {stats.get('total_bans',0)}\n🗑️ عدد الطرد: {stats.get('total_kicks',0)}"
        await message.reply(info, parse_mode="Markdown")
        return
    elif text.startswith("$تنبيه"):
        reason = text[8:].strip() or "لا يوجد سبب"
        await message.reply(f"⚠️ تم تنبيه {target_name}\nالسبب: {reason}")
        await send_advanced_notification(chat_id, executor_name, executor_role, target_name, "⚠️ تنبيه", reason)
        await update_user_stats(target.id, 'total_warns')
        return
    elif text.startswith("$كتم"):
        parts = text.split(maxsplit=2)
        duration_str = parts[1] if len(parts) >= 2 else "30m"
        reason = parts[2] if len(parts) > 2 else "لا يوجد سبب"
        duration_minutes = 0
        if duration_str.endswith('m'):
            duration_minutes = int(duration_str[:-1])
        elif duration_str.endswith('h'):
            duration_minutes = int(duration_str[:-1]) * 60
        elif duration_str.endswith('d'):
            duration_minutes = int(duration_str[:-1]) * 1440
        else:
            duration_minutes = int(duration_str) if duration_str.isdigit() else 30
        until = datetime.now() + timedelta(minutes=duration_minutes)
        await db.execute("INSERT INTO temp_bans (user_id, chat_id, until, reason) VALUES ($1, $2, $3, $4) ON CONFLICT (user_id, chat_id) DO UPDATE SET until=$3, reason=$4", target.id, chat_id, until, reason)
        await set_user_status(target.id, "muted")
        await message.reply(f"🔇 تم كتم {target_name} لمدة {duration_str}\nالسبب: {reason}")
        await send_advanced_notification(chat_id, executor_name, executor_role, target_name, "🔇 كتم", reason, duration_str)
        await update_user_stats(target.id, 'total_mutes')
        return
    elif text == "$فك كتم":
        await db.execute("DELETE FROM temp_bans WHERE user_id=$1 AND chat_id=$2", target.id, chat_id)
        await set_user_status(target.id, "active")
        await message.reply(f"🔈 تم فك الكتم عن {target_name}")
        await send_advanced_notification(chat_id, executor_name, executor_role, target_name, "🔈 فك كتم", "")
        return

    # الأوامر الخاصة بالأدمن فقط
    if not is_admin:
        return

    if text.startswith("$خصم"):
        parts = text.split(maxsplit=2)
        if len(parts) >= 2 and parts[1].isdigit():
            amount = int(parts[1])
            reason = parts[2] if len(parts) > 2 else "خصم بواسطة أدمن"
            await update_user_money(target.id, -amount, reason, user_id)
            await message.reply(f"✅ تم خصم {amount} {CURRENCY_NAME} من {target_name}")
            await send_advanced_notification(chat_id, executor_name, executor_role, target_name, "💰 خصم رصيد", f"-{amount} {CURRENCY_NAME}\nالسبب: {reason}")
            await update_user_stats(target.id, 'total_deductions', 1, (amount, reason))
        else:
            await message.reply("❌ استخدم: $خصم 50 سبب")
    elif text.startswith("$اعطاء") or text.startswith("$إعطاء"):
        parts = text.split(maxsplit=2)
        if len(parts) >= 2 and parts[1].isdigit():
            amount = int(parts[1])
            reason = parts[2] if len(parts) > 2 else "مكافأة"
            await update_user_money(target.id, amount, reason, user_id)
            await message.reply(f"✅ تم إضافة {amount} {CURRENCY_NAME} إلى {target_name}")
            await send_advanced_notification(chat_id, executor_name, executor_role, target_name, "💰 إضافة رصيد", f"+{amount} {CURRENCY_NAME}\nالسبب: {reason}")
        else:
            await message.reply("❌ استخدم: $اعطاء 100 سبب")
    elif text.startswith("$تحذير"):
        reason = text[8:].strip() or "لا يوجد سبب"
        user = await get_user(target.id)
        warnings = user['warnings'] + 1
        await db.execute("UPDATE users SET warnings = $1 WHERE telegram_id = $2", warnings, target.id)
        await message.reply(f"⚠️ تم تحذير {target_name} (التحذير {warnings}/3)\nالسبب: {reason}")
        await send_advanced_notification(chat_id, executor_name, executor_role, target_name, "⚠️ تحذير", f"التحذير {warnings}/3\nالسبب: {reason}")
        await update_user_stats(target.id, 'total_warns')
        if warnings >= 3:
            await set_user_status(target.id, "banned")
            await message.reply(f"🚫 تم حظر {target_name} تلقائياً")
            await send_advanced_notification(chat_id, executor_name, executor_role, target_name, "🚫 حظر تلقائي", "3 تحذيرات")
    elif text.startswith("$حظر"):
        reason = text[5:].strip() or "لا يوجد سبب"
        await set_user_status(target.id, "banned")
        await message.reply(f"🚫 تم حظر {target_name}")
        await send_advanced_notification(chat_id, executor_name, executor_role, target_name, "🚫 حظر", reason)
        await update_user_stats(target.id, 'total_bans')
    elif text == "$فك حظر":
        await set_user_status(target.id, "active")
        await message.reply(f"✅ تم فك الحظر عن {target_name}")
        await send_advanced_notification(chat_id, executor_name, executor_role, target_name, "✅ فك حظر", "")
    elif text.startswith("$طرد"):
        reason = text[5:].strip() or "لا يوجد سبب"
        await message.reply(f"👢 تم طرد {target_name}")
        await send_advanced_notification(chat_id, executor_name, executor_role, target_name, "🗑️ طرد", reason)
        await update_user_stats(target.id, 'total_kicks')
        try:
            await message.chat.ban_member(target.id)
            await message.chat.unban_member(target.id)
        except:
            pass
    elif text.startswith("$لقب"):
        new_title = text[5:].strip()
        if new_title:
            success = await set_user_title(target.id, new_title)
            if success:
                await message.reply(f"🏷️ تم منح اللقب '{new_title}' إلى {target_name}")
                await send_advanced_notification(chat_id, executor_name, executor_role, target_name, "🏷️ تغيير لقب", f"اللقب الجديد: {new_title}")
            else:
                await message.reply("❌ اللقب غير موجود في القائمة")
        else:
            await message.reply("❌ استخدم: $لقب بطل")
    elif text == "$سجل":
        rows = await db.fetch("SELECT * FROM economy_log WHERE admin_id = $1 ORDER BY timestamp DESC LIMIT 10", user_id)
        if rows:
            log = "📜 *آخر عملياتك:*\n"
            for row in rows:
                log += f"• {row['amount']} {CURRENCY_NAME} للمستخدم {row['user_id']} - {row['reason']}\n"
            await message.reply(log, parse_mode="Markdown")
        else:
            await message.reply("📭 لا توجد عمليات مسجلة لك.")

# ========== أوامر الأعضاء (#) ==========
async def handle_member_commands(message: Message):
    text = message.text.strip()
    user_id = message.from_user.id

    if text in ["#ملفي", "#حسابي", "#معلوماتي", "#معلومات", "#ملف"]:
        user = await get_user(user_id)
        progress = await get_xp_progress(user_id)
        stats = await get_user_stats(user_id)
        money_formatted = f"{user['money']:,}".replace(",", ".")
        reply = f"""╭━━━━━━━━━━━━━━━━━━━━━━╮
┃ 👤 *الملف الشخصي* 👤
╰━━━━━━━━━━━━━━━━━━━━━━╯

✨ *الاسم:* {user['full_name']}
🆔 *المعرف:* @{user['username'] or 'لا يوجد'}

━━━━━━━━━━━━━━━━━━━━━━
💰 *الرصيد:* {money_formatted} {CURRENCY_NAME}
🏆 *اللقب:* {user['title'] or 'لا يوجد'}
⭐ *النقاط (XP):* {user['xp']}
📊 *المستوى:* {user['level']}

📈 *شريط التقدم:*
{progress['bar']} {progress['percent']}%

⏳ *المتبقي للمستوى التالي:* {progress['remaining']} XP

━━━━━━━━━━━━━━━━━━━━━━
📨 *الرسائل:* {stats.get('total_messages',0)}
⚠️ *التحذيرات:* {stats.get('total_warns',0)}
🔇 *عدد مرات الكتم:* {stats.get('total_mutes',0)}
🚫 *عدد مرات الحظر:* {stats.get('total_bans',0)}
🗑️ *عدد مرات الطرد:* {stats.get('total_kicks',0)}
💰 *عدد الخصومات:* {stats.get('total_deductions',0)}
📝 *آخر خصم:* {stats.get('last_deduction_amount',0)} {CURRENCY_NAME} - {stats.get('last_deduction_reason','لا يوجد')}

━━━━━━━━━━━━━━━━━━━━━━
🎮 *نقاط الألعاب:* {user['game_points']}
🏅 *الفوز في الألعاب:* {user['wins']}"""
        await message.reply(reply, parse_mode="Markdown")
    elif text in ["#فلوس", "#فلوسي", "#رصيدي"]:
        user = await get_user(user_id)
        money_formatted = f"{user['money']:,}".replace(",", ".")
        await message.reply(f"💰 رصيدك الحالي: {money_formatted} {CURRENCY_NAME}")
    elif text in ["#لقب", "#لقبي", "#اللقب"]:
        user = await get_user(user_id)
        await message.reply(f"🏷️ لقبك: {user['title'] or 'لا يوجد'}")
    elif text in ["#لعبة", "#العب", "#العاب"]:
        await cmd_game(message)
    elif text in ["#مستواي", "#لـيفلي", "#نقاطي", "#مستوى", "#لفل"]:
        user = await get_user(user_id)
        progress = await get_xp_progress(user_id)
        await message.reply(f"📊 *المستوى {user['level']}*\n{progress['bar']} {progress['percent']}%\n{progress['remaining']} XP للمستوى التالي", parse_mode="Markdown")
    elif text in ["#شراء", "#محل", "#اسواق"]:
        from _core.callbacks import show_shop_menu
        await show_shop_menu(message)

# ========== إضافة XP عند كل رسالة ==========
async def add_xp_on_message(message: Message):
    if not message.text:
        return
    if message.text.startswith(("#", "$")):
        return
    if message.from_user.id in ADMIN_IDS:
        return
    await add_xp(message.from_user.id, XP_PER_MESSAGE, message.chat.id, message.from_user.full_name)
    await update_user_stats(message.from_user.id, 'total_messages')

def register_event_handlers(dp: Dispatcher):
    dp.message.register(handle_admin_commands, lambda msg: msg.text and msg.text.startswith("$"))
    dp.message.register(handle_member_commands, lambda msg: msg.text and msg.text.startswith("#"))
    dp.message.register(add_xp_on_message)
