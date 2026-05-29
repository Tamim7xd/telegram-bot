from aiogram import Dispatcher
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import Command
from config import ADMIN_IDS, CURRENCY_NAME
from db import db
from _core.users import update_user_money, set_user_status, get_user
from _core.titles import set_user_title
from _core.notify import bot

# دالة مساعدة لإرسال إشعار للمجموعة
async def send_group_notification(chat_id: int, admin_name: str, target_name: str, action: str, detail: str = ""):
    text = f"""╭━━━━━━━━━━━━━━━━━━━━━━╮
┃ 🔔 *إشـارة إداريـة* 🔔
╰━━━━━━━━━━━━━━━━━━━━━━╯

👤 *المشرف:* {admin_name}
👥 *المستخدم:* {target_name}
⚙️ *الإجراء:* {action}
📝 *التفاصيل:* {detail}

🕒 *الوقت:* الآن
━━━━━━━━━━━━━━━━━━━━━━"""
    await bot.send_message(chat_id, text, parse_mode="Markdown")

# ---------- لوحة الأدمن الرئيسية ----------
async def admin_panel(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.reply("⚠️ هذا الأمر للأدمن فقط.")
        return
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👥 إدارة الأعضاء", callback_data="admin_users_list")],
        [InlineKeyboardButton(text="💰 الاقتصاد", callback_data="admin_economy")],
        [InlineKeyboardButton(text="📊 الإحصائيات", callback_data="admin_stats")],
        [InlineKeyboardButton(text="❌ إغلاق", callback_data="admin_close")]
    ])
    await message.reply("👑 *لوحة تحكم الأدمن*\nاختر أحد الخيارات:", reply_markup=keyboard, parse_mode="Markdown")

# ---------- عرض قائمة الأعضاء بأزرار ----------
async def show_users_list(callback: CallbackQuery, page=1):
    limit = 10
    offset = (page - 1) * limit
    rows = await db.fetch(
        "SELECT telegram_id, full_name, username, money, level, status FROM users ORDER BY created_at DESC LIMIT $1 OFFSET $2",
        limit, offset
    )
    if not rows:
        await callback.message.edit_text("لا يوجد أعضاء بعد.")
        return
    buttons = []
    for r in rows:
        status_icon = "🟢" if r['status'] == 'active' else ("🔴" if r['status'] == 'banned' else "🟡")
        buttons.append([InlineKeyboardButton(text=f"{status_icon} {r['full_name']}", callback_data=f"admin_show_{r['telegram_id']}")])
    nav_btns = []
    if page > 1:
        nav_btns.append(InlineKeyboardButton(text="◀️ السابق", callback_data=f"users_page_{page-1}"))
    if len(rows) == limit:
        nav_btns.append(InlineKeyboardButton(text="التالي ▶️", callback_data=f"users_page_{page+1}"))
    if nav_btns:
        buttons.append(nav_btns)
    buttons.append([InlineKeyboardButton(text="◀️ رجوع للوحة", callback_data="admin_back")])
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.edit_text("👥 *اختر عضواً لإدارته:*", parse_mode="Markdown", reply_markup=keyboard)

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
🔹 *الحالة:* {user['status']}
━━━━━━━━━━━━━━━━━━━━━━"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ إضافة 100", callback_data=f"admin_addmoney_{user_id}_100"),
         InlineKeyboardButton(text="➖ خصم 50", callback_data=f"admin_removemoney_{user_id}_50")],
        [InlineKeyboardButton(text="🔇 كتم", callback_data=f"admin_mute_{user_id}"),
         InlineKeyboardButton(text="🔈 فك الكتم", callback_data=f"admin_unmute_{user_id}")],
        [InlineKeyboardButton(text="🚫 حظر", callback_data=f"admin_ban_{user_id}"),
         InlineKeyboardButton(text="✅ إلغاء الحظر", callback_data=f"admin_unban_{user_id}")],
        [InlineKeyboardButton(text="🏷️ تغيير اللقب", callback_data=f"admin_settitle_{user_id}"),
         InlineKeyboardButton(text="🗑️ طرد", callback_data=f"admin_kick_{user_id}")],
        [InlineKeyboardButton(text="◀️ رجوع للقائمة", callback_data="admin_users_list")]
    ])
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)

# ---------- المعالج الرئيسي للأزرار ----------
async def process_admin_callback(callback: CallbackQuery):
    user_id = callback.from_user.id
    if user_id not in ADMIN_IDS:
        await callback.answer("غير مصرح", show_alert=True)
        return
    data = callback.data
    await callback.answer("✅")
    chat_id = callback.message.chat.id
    admin_name = callback.from_user.full_name

    # التنقل بين الصفحات
    if data.startswith("users_page_"):
        page = int(data.split("_")[-1])
        await show_users_list(callback, page)
        return
    if data == "admin_users_list":
        await show_users_list(callback, 1)
        return
    if data == "admin_back":
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="👥 إدارة الأعضاء", callback_data="admin_users_list")],
            [InlineKeyboardButton(text="💰 الاقتصاد", callback_data="admin_economy")],
            [InlineKeyboardButton(text="📊 الإحصائيات", callback_data="admin_stats")],
            [InlineKeyboardButton(text="❌ إغلاق", callback_data="admin_close")]
        ])
        await callback.message.edit_text("👑 *لوحة تحكم الأدمن*", parse_mode="Markdown", reply_markup=keyboard)
        return
    if data == "admin_economy":
        total = await db.fetchval("SELECT SUM(money) FROM users") or 0
        count = await db.fetchval("SELECT COUNT(*) FROM users") or 0
        text = f"💰 *الاقتصاد*\nإجمالي الأموال: {total} {CURRENCY_NAME}\nعدد المستخدمين: {count}"
        await callback.message.edit_text(text, parse_mode="Markdown")
        back = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ رجوع", callback_data="admin_back")]])
        await callback.message.edit_reply_markup(reply_markup=back)
        return
    if data == "admin_stats":
        msgs = await db.fetchval("SELECT SUM(messages_count) FROM users") or 0
        wins = await db.fetchval("SELECT SUM(wins) FROM users") or 0
        top = await db.fetchrow("SELECT full_name, money FROM users ORDER BY money DESC LIMIT 1")
        top_text = f"🏆 الأغنى: {top['full_name']} (💰{top['money']})" if top else ""
        text = f"📊 *إحصائيات*\nالرسائل: {msgs}\nالانتصارات: {wins}\n{top_text}"
        await callback.message.edit_text(text, parse_mode="Markdown")
        back = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ رجوع", callback_data="admin_back")]])
        await callback.message.edit_reply_markup(reply_markup=back)
        return
    if data == "admin_close":
        await callback.message.delete()
        return

    # عرض صفحة تحكم العضو
    if data.startswith("admin_show_"):
        target_id = int(data.split("_")[-1])
        await show_user_controls(callback, target_id)
        return

    # ------------------- إجراءات التحكم -------------------
    # إضافة رصيد
    if data.startswith("admin_addmoney_"):
        parts = data.split("_")
        target_id = int(parts[2])
        amount = int(parts[3])
        target_user = await get_user(target_id)
        await update_user_money(target_id, amount, "إضافة عن طريق لوحة الأدمن", user_id)
        await callback.message.answer(f"✅ تم إضافة {amount} {CURRENCY_NAME} للمستخدم.")
        await send_group_notification(chat_id, admin_name, target_user['full_name'], "💰 إضافة رصيد", f"+{amount} {CURRENCY_NAME}")
        await show_user_controls(callback, target_id)
        return

    # خصم رصيد
    if data.startswith("admin_removemoney_"):
        parts = data.split("_")
        target_id = int(parts[2])
        amount = int(parts[3])
        target_user = await get_user(target_id)
        await update_user_money(target_id, -amount, "خصم عن طريق لوحة الأدمن", user_id)
        await callback.message.answer(f"✅ تم خصم {amount} {CURRENCY_NAME} من المستخدم.")
        await send_group_notification(chat_id, admin_name, target_user['full_name'], "💰 خصم رصيد", f"-{amount} {CURRENCY_NAME}")
        await show_user_controls(callback, target_id)
        return

    # كتم
    if data.startswith("admin_mute_"):
        target_id = int(data.split("_")[-1])
        target_user = await get_user(target_id)
        await set_user_status(target_id, "muted")
        await callback.message.answer("🔇 تم كتم المستخدم.")
        await send_group_notification(chat_id, admin_name, target_user['full_name'], "🔇 كتم", "تم كتم المستخدم")
        await show_user_controls(callback, target_id)
        return

    # فك الكتم
    if data.startswith("admin_unmute_"):
        target_id = int(data.split("_")[-1])
        target_user = await get_user(target_id)
        await set_user_status(target_id, "active")
        await callback.message.answer("🔈 تم فك الكتم.")
        await send_group_notification(chat_id, admin_name, target_user['full_name'], "🔈 فك كتم", "تم فك الكتم عن المستخدم")
        await show_user_controls(callback, target_id)
        return

    # حظر
    if data.startswith("admin_ban_"):
        target_id = int(data.split("_")[-1])
        target_user = await get_user(target_id)
        await set_user_status(target_id, "banned")
        await callback.message.answer("🚫 تم حظر المستخدم.")
        await send_group_notification(chat_id, admin_name, target_user['full_name'], "🚫 حظر", "تم حظر المستخدم من البوت")
        await show_user_controls(callback, target_id)
        return

    # إلغاء الحظر
    if data.startswith("admin_unban_"):
        target_id = int(data.split("_")[-1])
        target_user = await get_user(target_id)
        await set_user_status(target_id, "active")
        await callback.message.answer("✅ تم إلغاء الحظر.")
        await send_group_notification(chat_id, admin_name, target_user['full_name'], "✅ إلغاء حظر", "تم إلغاء حظر المستخدم")
        await show_user_controls(callback, target_id)
        return

    # طرد من المجموعة
    if data.startswith("admin_kick_"):
        target_id = int(data.split("_")[-1])
        target_user = await get_user(target_id)
        try:
            await callback.message.chat.ban_member(target_id)
            await callback.message.chat.unban_member(target_id)
            await callback.message.answer("🗑️ تم طرد العضو من المجموعة.")
            await send_group_notification(chat_id, admin_name, target_user['full_name'], "🗑️ طرد", "تم طرد العضو من المجموعة")
        except:
            await callback.message.answer("❌ فشل الطرد (قد لا يمتلك البوت صلاحية الطرد).")
        await show_user_controls(callback, target_id)
        return

    # تغيير اللقب (يطلب إدخال اللقب)
    if data.startswith("admin_settitle_"):
        target_id = int(data.split("_")[-1])
        # سنقوم بإرسال رسالة منفصلة لاستقبال اللقب
        await callback.message.answer(f"أرسل اللقب الجديد للمستخدم (ID: {target_id}) في رسالة منفردة.")
        # يمكن تفعيل FSM هنا، لكن للتبسيط سنعتمد على معالج منفصل (يمكن إضافته لاحقًا)
        return

def register_callback_handlers(dp: Dispatcher):
    dp.message.register(admin_panel, Command("adminiq"))
    dp.callback_query.register(process_admin_callback, lambda c: c.data and c.data.startswith("admin_"))
