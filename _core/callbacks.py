from aiogram import Dispatcher, types
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import Command
from config import ADMIN_IDS, CURRENCY_NAME
from db import db
from _core.users import get_user, update_user_money, set_user_status
from _core.titles import set_user_title, get_available_titles, add_custom_title
from _core.notify import bot

# دالة إرسال إشعار إداري للمجموعة
async def log_admin_action(chat_id: int, admin_name: str, target_name: str, action: str, detail: str = ""):
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
        [InlineKeyboardButton(text="👥 إدارة الأعضاء", callback_data="admin_users")],
        [InlineKeyboardButton(text="💰 الاقتصاد", callback_data="admin_economy")],
        [InlineKeyboardButton(text="🏆 الألقاب", callback_data="admin_titles")],
        [InlineKeyboardButton(text="📊 الإحصائيات", callback_data="admin_stats")],
        [InlineKeyboardButton(text="📣 إعلان جماعي", callback_data="admin_announce")],
        [InlineKeyboardButton(text="📌 إدارة المجموعة", callback_data="admin_group")],
        [InlineKeyboardButton(text="❌ إغلاق", callback_data="admin_close")]
    ])
    await message.reply("👑 *لوحة تحكم الأدمن*\nاختر أحد الخيارات:", reply_markup=keyboard, parse_mode="Markdown")

# ---------- عرض قائمة الأعضاء بأسماء قابلة للنقر ----------
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
🔹 *الحالة:* {user['status']}
━━━━━━━━━━━━━━━━━━━━━━"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ إضافة 100", callback_data=f"add_{user_id}_100"),
         InlineKeyboardButton(text="➖ خصم 50", callback_data=f"sub_{user_id}_50")],
        [InlineKeyboardButton(text="🔇 كتم", callback_data=f"mute_{user_id}"),
         InlineKeyboardButton(text="🔈 فك كتم", callback_data=f"unmute_{user_id}")],
        [InlineKeyboardButton(text="🚫 حظر", callback_data=f"ban_{user_id}"),
         InlineKeyboardButton(text="✅ فك حظر", callback_data=f"unban_{user_id}")],
        [InlineKeyboardButton(text="🏷️ تغيير اللقب", callback_data=f"change_title_{user_id}")],
        [InlineKeyboardButton(text="◀️ رجوع", callback_data="users_list")]
    ])
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)

# ---------- عرض قائمة الألقاب المتاحة ----------
async def show_titles_list(callback: CallbackQuery):
    titles = await get_available_titles()
    if not titles:
        titles = ["عضو", "مقاتل", "محارب", "بطل", "أسطورة"]
    text = "🏆 *الألقاب المتاحة:*\n" + "\n".join([f"• {t}" for t in titles[:20]])
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ إضافة لقب جديد", callback_data="add_new_title")],
        [InlineKeyboardButton(text="◀️ رجوع", callback_data="back_main")]
    ])
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)

# ---------- إرسال إعلان جماعي ----------
async def broadcast_message(admin_id: int, message_text: str):
    users = await db.fetch("SELECT telegram_id FROM users")
    count = 0
    for user in users:
        try:
            await bot.send_message(user['telegram_id'], f"📢 *إعلان من الإدارة:*\n\n{message_text}", parse_mode="Markdown")
            count += 1
        except:
            pass
    return count

# ---------- المعالج الرئيسي للأزرار ----------
async def process_callback(callback: CallbackQuery):
    await callback.answer()
    data = callback.data
    admin_id = callback.from_user.id
    chat_id = callback.message.chat.id
    admin_name = callback.from_user.full_name

    if admin_id not in ADMIN_IDS and not data.startswith(("user_", "back_main", "users_page_")):
        await callback.message.answer("❌ غير مصرح لك.")
        return

    # عرض قائمة الأعضاء
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
    # الألقاب
    if data == "admin_titles":
        await show_titles_list(callback)
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
    # إعلان جماعي
    if data == "admin_announce":
        await callback.message.edit_text("📣 أرسل نص الإعلان الآن (سيتم إرساله لجميع المستخدمين).")
        # سنستخدم FSM لاحقاً، لكن للتبسيط سنعتبر أن الإعلان يرسل من أمر منفصل
        back = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ رجوع", callback_data="back_main")]])
        await callback.message.edit_reply_markup(reply_markup=back)
        return
    # إدارة المجموعة (إرسال، تثبيت، حذف)
    if data == "admin_group":
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📨 إرسال رسالة للمجموعة", callback_data="group_send")],
            [InlineKeyboardButton(text="📌 تثبيت رسالة", callback_data="group_pin")],
            [InlineKeyboardButton(text="🗑️ حذف رسالة", callback_data="group_delete")],
            [InlineKeyboardButton(text="◀️ رجوع", callback_data="back_main")]
        ])
        await callback.message.edit_text("📌 *إدارة المجموعة*", parse_mode="Markdown", reply_markup=keyboard)
        return
    # إرسال رسالة للمجموعة
    if data == "group_send":
        await callback.message.edit_text("أرسل النص الذي تريد إرساله للمجموعة:")
        # سيتم استقبال النص في معالج منفصل
        back = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ رجوع", callback_data="admin_group")]])
        await callback.message.edit_reply_markup(reply_markup=back)
        return
    # تثبيت رسالة
    if data == "group_pin":
        await callback.message.edit_text("قم بالرد على الرسالة التي تريد تثبيتها بكلمة `/pin`")
        back = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ رجوع", callback_data="admin_group")]])
        await callback.message.edit_reply_markup(reply_markup=back)
        return
    # حذف رسالة
    if data == "group_delete":
        await callback.message.edit_text("قم بالرد على الرسالة التي تريد حذفها بكلمة `/del`")
        back = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ رجوع", callback_data="admin_group")]])
        await callback.message.edit_reply_markup(reply_markup=back)
        return
    # إغلاق اللوحة
    if data == "admin_close":
        await callback.message.delete()
        return
    # العودة للوحة الرئيسية
    if data == "back_main":
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="👥 إدارة الأعضاء", callback_data="admin_users")],
            [InlineKeyboardButton(text="💰 الاقتصاد", callback_data="admin_economy")],
            [InlineKeyboardButton(text="🏆 الألقاب", callback_data="admin_titles")],
            [InlineKeyboardButton(text="📊 الإحصائيات", callback_data="admin_stats")],
            [InlineKeyboardButton(text="📣 إعلان جماعي", callback_data="admin_announce")],
            [InlineKeyboardButton(text="📌 إدارة المجموعة", callback_data="admin_group")],
            [InlineKeyboardButton(text="❌ إغلاق", callback_data="admin_close")]
        ])
        await callback.message.edit_text("👑 *لوحة تحكم الأدمن*", parse_mode="Markdown", reply_markup=keyboard)
        return
    # الصفحات
    if data.startswith("users_page_"):
        page = int(data.split("_")[-1])
        await show_users_list(callback, page)
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

    # ------------------- إجراءات التحكم -------------------
    if data.startswith("add_"):
        parts = data.split("_")
        target_id = int(parts[1])
        amount = int(parts[2])
        target_user = await get_user(target_id)
        await update_user_money(target_id, amount, "إضافة عبر لوحة التحكم", admin_id)
        await callback.message.answer(f"✅ تم إضافة {amount} {CURRENCY_NAME}")
        await log_admin_action(chat_id, admin_name, target_user['full_name'], "💰 إضافة رصيد", f"+{amount} {CURRENCY_NAME}")
        await show_user_controls(callback, target_id)
        return
    if data.startswith("sub_"):
        parts = data.split("_")
        target_id = int(parts[1])
        amount = int(parts[2])
        target_user = await get_user(target_id)
        await update_user_money(target_id, -amount, "خصم عبر لوحة التحكم", admin_id)
        await callback.message.answer(f"✅ تم خصم {amount} {CURRENCY_NAME}")
        await log_admin_action(chat_id, admin_name, target_user['full_name'], "💰 خصم رصيد", f"-{amount} {CURRENCY_NAME}")
        await show_user_controls(callback, target_id)
        return
    if data.startswith("mute_"):
        target_id = int(data.split("_")[1])
        target_user = await get_user(target_id)
        await set_user_status(target_id, "muted")
        await callback.message.answer("🔇 تم كتم المستخدم")
        await log_admin_action(chat_id, admin_name, target_user['full_name'], "🔇 كتم", "تم كتم المستخدم")
        await show_user_controls(callback, target_id)
        return
    if data.startswith("unmute_"):
        target_id = int(data.split("_")[1])
        target_user = await get_user(target_id)
        await set_user_status(target_id, "active")
        await callback.message.answer("🔈 تم فك الكتم")
        await log_admin_action(chat_id, admin_name, target_user['full_name'], "🔈 فك كتم", "تم فك الكتم عن المستخدم")
        await show_user_controls(callback, target_id)
        return
    if data.startswith("ban_"):
        target_id = int(data.split("_")[1])
        target_user = await get_user(target_id)
        await set_user_status(target_id, "banned")
        await callback.message.answer("🚫 تم حظر المستخدم")
        await log_admin_action(chat_id, admin_name, target_user['full_name'], "🚫 حظر", "تم حظر المستخدم من البوت")
        await show_user_controls(callback, target_id)
        return
    if data.startswith("unban_"):
        target_id = int(data.split("_")[1])
        target_user = await get_user(target_id)
        await set_user_status(target_id, "active")
        await callback.message.answer("✅ تم فك الحظر")
        await log_admin_action(chat_id, admin_name, target_user['full_name'], "✅ فك حظر", "تم إلغاء حظر المستخدم")
        await show_user_controls(callback, target_id)
        return
    if data.startswith("change_title_"):
        target_id = int(data.split("_")[2] if len(data.split("_")) > 2 else data.split("_")[1])
        await callback.message.answer(f"أرسل اللقب الجديد للمستخدم (ID: {target_id})")
        # هنا يمكن تفعيل FSM، لكن للتبسيط سيتم استقبال اللقب في معالج منفصل
        return

def register_callback_handlers(dp: Dispatcher):
    dp.message.register(admin_panel, Command("adminiq"))
    dp.callback_query.register(process_callback)
