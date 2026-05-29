from aiogram import Dispatcher
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import Command
from config import ADMIN_IDS, CURRENCY_NAME
from db import db
from _core.users import get_user, update_user_money, set_user_status
from _core.titles import set_user_title
from _core.notify import bot

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

# ---------- لوحة الأدمن الرئيسية ----------
async def admin_panel(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.reply("⚠️ هذا الأمر للأدمن فقط.")
        return
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👥 إدارة الأعضاء", callback_data="admin_users")],
        [InlineKeyboardButton(text="💰 الاقتصاد", callback_data="admin_economy")],
        [InlineKeyboardButton(text="📊 الإحصائيات", callback_data="admin_stats")],
        [InlineKeyboardButton(text="❌ إغلاق", callback_data="admin_close")]
    ])
    await message.reply("👑 *لوحة تحكم الأدمن*", reply_markup=keyboard, parse_mode="Markdown")

# ---------- عرض قائمة الأعضاء (أسماء قابلة للنقر) ----------
async def show_users_list(callback: CallbackQuery, page=1):
    limit = 10
    offset = (page - 1) * limit
    rows = await db.fetch(
        "SELECT telegram_id, full_name, money, level FROM users ORDER BY created_at DESC LIMIT $1 OFFSET $2",
        limit, offset
    )
    if not rows:
        await callback.message.edit_text("لا يوجد أعضاء بعد.")
        return
    buttons = []
    for r in rows:
        buttons.append([InlineKeyboardButton(text=f"{r['full_name']} (💰{r['money']})", callback_data=f"user_{r['telegram_id']}")])
    nav_btns = []
    if page > 1:
        nav_btns.append(InlineKeyboardButton(text="◀️ السابق", callback_data=f"users_page_{page-1}"))
    if len(rows) == limit:
        nav_btns.append(InlineKeyboardButton(text="التالي ▶️", callback_data=f"users_page_{page+1}"))
    if nav_btns:
        buttons.append(nav_btns)
    buttons.append([InlineKeyboardButton(text="◀️ رجوع", callback_data="back_main")])
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.edit_text("👥 *اختر عضواً:*", parse_mode="Markdown", reply_markup=keyboard)

# ---------- عرض تفاصيل العضو وأزرار التحكم ----------
async def show_user_controls(callback: CallbackQuery, user_id: int):
    user = await get_user(user_id)
    if not user:
        await callback.answer("المستخدم غير موجود")
        return
    text = f"""╭━━━━━━━━━━━━━━━━━━━━━━╮
┃ 👤 *ملف العضو* 👤
╰━━━━━━━━━━━━━━━━━━━━━━╯

✨ *الاسم:* {user['full_name']}
🆔 *المعرف:* @{user['username'] or 'لا يوجد'}
━━━━━━━━━━━━━━━━━━━━━━
💰 *الرصيد:* {user['money']} {CURRENCY_NAME}
⭐ *XP:* {user['xp']}
📊 *المستوى:* {user['level']}
🏷️ *اللقب:* {user['title'] or 'لا يوجد'}
🔹 *الحالة:* {user['status']}"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ إضافة 100", callback_data=f"add_{user_id}_100"),
         InlineKeyboardButton(text="➖ خصم 50", callback_data=f"sub_{user_id}_50")],
        [InlineKeyboardButton(text="🔇 كتم", callback_data=f"mute_{user_id}"),
         InlineKeyboardButton(text="🔈 فك كتم", callback_data=f"unmute_{user_id}")],
        [InlineKeyboardButton(text="🚫 حظر", callback_data=f"ban_{user_id}"),
         InlineKeyboardButton(text="✅ فك حظر", callback_data=f"unban_{user_id}")],
        [InlineKeyboardButton(text="🏷️ تغيير اللقب", callback_data=f"title_{user_id}")],
        [InlineKeyboardButton(text="🗑️ طرد", callback_data=f"kick_{user_id}")],
        [InlineKeyboardButton(text="◀️ رجوع", callback_data="users_list")]
    ])
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)

# ---------- المعالج الرئيسي لجميع الأزرار ----------
async def process_callback(callback: CallbackQuery):
    await callback.answer()
    data = callback.data
    admin_id = callback.from_user.id
    chat_id = callback.message.chat.id
    admin_name = callback.from_user.full_name

    if admin_id not in ADMIN_IDS and not data.startswith(("user_", "back_main", "users_page_", "users_list")):
        await callback.message.answer("❌ غير مصرح.")
        return

    # الصفحات
    if data.startswith("users_page_"):
        page = int(data.split("_")[-1])
        await show_users_list(callback, page)
        return
    # قائمة الأعضاء
    if data == "admin_users":
        await show_users_list(callback, 1)
        return
    # الاقتصاد
    if data == "admin_economy":
        total = await db.fetchval("SELECT SUM(money) FROM users") or 0
        count = await db.fetchval("SELECT COUNT(*) FROM users") or 0
        text = f"💰 *الاقتصاد*\nإجمالي الأموال: {total} {CURRENCY_NAME}\nعدد المستخدمين: {count}"
        await callback.message.edit_text(text, parse_mode="Markdown")
        back = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ رجوع", callback_data="back_main")]])
        await callback.message.edit_reply_markup(reply_markup=back)
        return
    # الإحصائيات
    if data == "admin_stats":
        msgs = await db.fetchval("SELECT SUM(messages_count) FROM users") or 0
        wins = await db.fetchval("SELECT SUM(wins) FROM users") or 0
        top = await db.fetchrow("SELECT full_name, money FROM users ORDER BY money DESC LIMIT 1")
        top_text = f"🏆 الأغنى: {top['full_name']} (💰{top['money']})" if top else ""
        text = f"📊 *الإحصائيات*\nالرسائل: {msgs}\nالانتصارات: {wins}\n{top_text}"
        await callback.message.edit_text(text, parse_mode="Markdown")
        back = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ رجوع", callback_data="back_main")]])
        await callback.message.edit_reply_markup(reply_markup=back)
        return
    # إغلاق
    if data == "admin_close":
        await callback.message.delete()
        return
    # رجوع
    if data == "back_main":
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="👥 إدارة الأعضاء", callback_data="admin_users")],
            [InlineKeyboardButton(text="💰 الاقتصاد", callback_data="admin_economy")],
            [InlineKeyboardButton(text="📊 الإحصائيات", callback_data="admin_stats")],
            [InlineKeyboardButton(text="❌ إغلاق", callback_data="admin_close")]
        ])
        await callback.message.edit_text("👑 *لوحة تحكم الأدمن*", parse_mode="Markdown", reply_markup=keyboard)
        return
    # اختيار مستخدم
    if data.startswith("user_"):
        target_id = int(data.split("_")[1])
        await show_user_controls(callback, target_id)
        return
    # رجوع لقائمة المستخدمين
    if data == "users_list":
        await show_users_list(callback, 1)
        return

    # إجراءات التحكم (تتم هنا)
    target_id = None
    if data.startswith("add_"):
        parts = data.split("_")
        target_id = int(parts[1])
        amount = int(parts[2])
        target = await get_user(target_id)
        await update_user_money(target_id, amount, "إضافة من اللوحة", admin_id)
        await callback.message.answer(f"✅ تم إضافة {amount} {CURRENCY_NAME}")
        await send_admin_notification(chat_id, admin_name, target['full_name'], "💰 إضافة رصيد", f"+{amount} {CURRENCY_NAME}")
    elif data.startswith("sub_"):
        parts = data.split("_")
        target_id = int(parts[1])
        amount = int(parts[2])
        target = await get_user(target_id)
        await update_user_money(target_id, -amount, "خصم من اللوحة", admin_id)
        await callback.message.answer(f"✅ تم خصم {amount} {CURRENCY_NAME}")
        await send_admin_notification(chat_id, admin_name, target['full_name'], "💰 خصم رصيد", f"-{amount} {CURRENCY_NAME}")
    elif data.startswith("mute_"):
        target_id = int(data.split("_")[1])
        target = await get_user(target_id)
        await set_user_status(target_id, "muted")
        await callback.message.answer("🔇 تم الكتم")
        await send_admin_notification(chat_id, admin_name, target['full_name'], "🔇 كتم", "")
    elif data.startswith("unmute_"):
        target_id = int(data.split("_")[1])
        target = await get_user(target_id)
        await set_user_status(target_id, "active")
        await callback.message.answer("🔈 تم فك الكتم")
        await send_admin_notification(chat_id, admin_name, target['full_name'], "🔈 فك كتم", "")
    elif data.startswith("ban_"):
        target_id = int(data.split("_")[1])
        target = await get_user(target_id)
        await set_user_status(target_id, "banned")
        await callback.message.answer("🚫 تم الحظر")
        await send_admin_notification(chat_id, admin_name, target['full_name'], "🚫 حظر", "")
    elif data.startswith("unban_"):
        target_id = int(data.split("_")[1])
        target = await get_user(target_id)
        await set_user_status(target_id, "active")
        await callback.message.answer("✅ تم فك الحظر")
        await send_admin_notification(chat_id, admin_name, target['full_name'], "✅ فك حظر", "")
    elif data.startswith("kick_"):
        target_id = int(data.split("_")[1])
        target = await get_user(target_id)
        await callback.message.answer("🗑️ تم الطرد")
        await send_admin_notification(chat_id, admin_name, target['full_name'], "🗑️ طرد", "")
        try:
            await callback.message.chat.ban_member(target_id)
            await callback.message.chat.unban_member(target_id)
        except:
            pass
    elif data.startswith("title_"):
        target_id = int(data.split("_")[1])
        await callback.message.answer(f"أرسل اللقب الجديد للمستخدم (ID: {target_id}) في رسالة منفردة.")
        # يمكن تفعيل FSM هنا
        return

    if target_id:
        await show_user_controls(callback, target_id)

def register_callback_handlers(dp: Dispatcher):
    dp.message.register(admin_panel, Command("adminiq"))
    dp.callback_query.register(process_callback)
