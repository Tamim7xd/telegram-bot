from aiogram import Dispatcher
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import Command
from config import ADMIN_IDS, CURRENCY_NAME
from db import db
from _core.users import get_user, update_user_money, set_user_status
from _core.titles import set_user_title, get_available_titles
from _core.notify import bot
from datetime import datetime

# ---------- إشعار إداري ----------
async def send_admin_notification(chat_id: int, admin_name: str, target_name: str, action: str, detail: str = ""):
    text = f"""╭━━━━━━━━━━━━━━━━━━━━━━━━━━╮
┃ 🔔 *إشـارة إداريـة* 🔔
╰━━━━━━━━━━━━━━━━━━━━━━━━━━╯

👤 *المشرف:* {admin_name}
👥 *المستخدم:* {target_name}
⚙️ *الإجراء:* {action}
📝 *التفاصيل:* {detail}
🕒 *الوقت:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
━━━━━━━━━━━━━━━━━━━━━━━━━━"""
    await bot.send_message(chat_id, text, parse_mode="Markdown")

# ---------- لوحة الأدمن الرئيسية (متطورة) ----------
async def admin_panel(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.reply("⚠️ هذا الأمر للأدمن فقط.")
        return
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👥 إدارة الأعضاء", callback_data="admin_users")],
        [InlineKeyboardButton(text="💰 الاقتصاد", callback_data="admin_economy")],
        [InlineKeyboardButton(text="🏷️ إدارة الألقاب", callback_data="admin_titles")],
        [InlineKeyboardButton(text="🛡️ المشرفون", callback_data="admin_mods")],
        [InlineKeyboardButton(text="🎮 إعدادات الألعاب", callback_data="admin_games")],
        [InlineKeyboardButton(text="📣 إعلان جماعي", callback_data="admin_broadcast")],
        [InlineKeyboardButton(text="📊 إحصائيات متقدمة", callback_data="admin_advanced_stats")],
        [InlineKeyboardButton(text="📌 إدارة المجموعة", callback_data="admin_group")],
        [InlineKeyboardButton(text="🏪 إدارة السوق", callback_data="admin_shop")],
        [InlineKeyboardButton(text="⚙️ الإعدادات العامة", callback_data="admin_settings")],
        [InlineKeyboardButton(text="❌ إغلاق", callback_data="admin_close")]
    ])
    await message.reply("👑 *لوحة تحكم الأدمن المتكاملة*", reply_markup=keyboard, parse_mode="Markdown")

# ---------- عرض قائمة الأعضاء (مع أزرار تحكم) ----------
async def show_users_list(callback: CallbackQuery, page=1):
    limit = 10
    offset = (page - 1) * limit
    rows = await db.fetch(
        "SELECT telegram_id, full_name, money, level, status FROM users ORDER BY created_at DESC LIMIT $1 OFFSET $2",
        limit, offset
    )
    if not rows:
        await callback.message.edit_text("لا يوجد أعضاء بعد.")
        return
    text = "👥 *قائمة الأعضاء*\n\n"
    buttons = []
    for r in rows:
        status_icon = "🟢" if r['status'] == 'active' else ("🔴" if r['status'] == 'banned' else "🟡")
        text += f"{status_icon} [{r['full_name']}](tg://user?id={r['telegram_id']}) - 💰{r['money']} - مستوى {r['level']}\n"
        buttons.append([InlineKeyboardButton(text=f"{status_icon} {r['full_name']}", callback_data=f"admin_show_{r['telegram_id']}")])
    # أزرار التنقل
    nav = []
    if page > 1:
        nav.append(InlineKeyboardButton(text="◀️ السابق", callback_data=f"users_page_{page-1}"))
    if len(rows) == limit:
        nav.append(InlineKeyboardButton(text="التالي ▶️", callback_data=f"users_page_{page+1}"))
    if nav:
        buttons.append(nav)
    buttons.append([InlineKeyboardButton(text="◀️ رجوع للوحة", callback_data="admin_back")])
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)

# ---------- عرض تفاصيل العضو مع أزرار التحكم ----------
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
        [InlineKeyboardButton(text="📜 سجل العمليات", callback_data=f"user_log_{user_id}")],
        [InlineKeyboardButton(text="◀️ رجوع للقائمة", callback_data="admin_users")]
    ])
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)

# ---------- عرض سجل عمليات العضو ----------
async def show_user_log(callback: CallbackQuery, user_id: int):
    rows = await db.fetch("SELECT * FROM economy_log WHERE user_id = $1 ORDER BY timestamp DESC LIMIT 10", user_id)
    if not rows:
        await callback.message.edit_text("لا توجد عمليات لهذا المستخدم.")
        return
    text = "📜 *سجل عمليات المستخدم:*\n\n"
    for r in rows:
        text += f"• {r['amount']} {CURRENCY_NAME} - {r['reason']} (بواسطة {r['admin_id']}) - {r['timestamp']}\n"
    back = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ رجوع", callback_data=f"admin_show_{user_id}")]])
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=back)

# ---------- إدارة الألقاب (إضافة/حذف) ----------
async def show_titles_management(callback: CallbackQuery):
    titles = await get_available_titles()
    text = "🏷️ *الألقاب المتاحة:*\n"
    for t in titles[:20]:
        text += f"• {t}\n"
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ إضافة لقب جديد", callback_data="add_title")],
        [InlineKeyboardButton(text="❌ حذف لقب", callback_data="del_title")],
        [InlineKeyboardButton(text="◀️ رجوع", callback_data="admin_back")]
    ])
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)

# ---------- إدارة المشرفين ----------
async def show_mods_list(callback: CallbackQuery):
    rows = await db.fetch("SELECT user_id FROM mods")
    text = "🛡️ *المشرفون الحاليون:*\n"
    for r in rows:
        user = await get_user(r['user_id'])
        text += f"• {user['full_name']} (ID: {r['user_id']})\n"
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ إضافة مشرف", callback_data="add_mod")],
        [InlineKeyboardButton(text="❌ إزالة مشرف", callback_data="remove_mod")],
        [InlineKeyboardButton(text="◀️ رجوع", callback_data="admin_back")]
    ])
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)

# ---------- إعدادات الألعاب ----------
async def show_game_settings(callback: CallbackQuery):
    # قراءة الإعدادات الحالية (يمكن تخزينها في جدول settings)
    text = "🎮 *إعدادات الألعاب*\n\n⚡ وقت كل لعبة: 20 ثانية\n💰 الجائزة الصغرى: 50 دينار\n💰 الجائزة الكبرى: 300 دينار\n✅ الألعاب مفعلة"
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="تعديل الوقت", callback_data="set_game_time"),
         InlineKeyboardButton(text="تعديل الجوائز", callback_data="set_game_prizes")],
        [InlineKeyboardButton(text="تعطيل/تفعيل الألعاب", callback_data="toggle_games")],
        [InlineKeyboardButton(text="◀️ رجوع", callback_data="admin_back")]
    ])
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)

# ---------- إدارة السوق (تعديل الرتب) ----------
async def show_shop_management(callback: CallbackQuery):
    items = await db.fetch("SELECT id, name, price, rank_level FROM shop_items ORDER BY rank_level")
    text = "🏪 *إدارة السوق*\n\n"
    for it in items:
        text += f"ID: {it['id']} - {it['name']} - 💰{it['price']} - مستوى {it['rank_level']}\n"
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ إضافة رتبة", callback_data="shop_add")],
        [InlineKeyboardButton(text="✏️ تعديل سعر", callback_data="shop_edit")],
        [InlineKeyboardButton(text="❌ حذف رتبة", callback_data="shop_del")],
        [InlineKeyboardButton(text="◀️ رجوع", callback_data="admin_back")]
    ])
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)

# ---------- الإحصائيات المتقدمة ----------
async def advanced_stats(callback: CallbackQuery):
    total_users = await db.fetchval("SELECT COUNT(*) FROM users") or 0
    total_money = await db.fetchval("SELECT SUM(money) FROM users") or 0
    total_msgs = await db.fetchval("SELECT SUM(messages_count) FROM users") or 0
    total_wins = await db.fetchval("SELECT SUM(wins) FROM users") or 0
    active_users = await db.fetchval("SELECT COUNT(*) FROM users WHERE status = 'active'") or 0
    banned_users = await db.fetchval("SELECT COUNT(*) FROM users WHERE status = 'banned'") or 0
    text = f"📊 *إحصائيات متقدمة*\n\n👥 إجمالي المستخدمين: {total_users}\n🟢 النشطاء: {active_users}\n🔴 المحظورون: {banned_users}\n💰 إجمالي الأموال: {total_money}\n📨 إجمالي الرسائل: {total_msgs}\n🏆 إجمالي الانتصارات: {total_wins}"
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ رجوع", callback_data="admin_back")]])
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)

# ---------- إدارة المجموعة (إرسال، تثبيت، حذف) ----------
async def group_management(callback: CallbackQuery):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📨 إرسال رسالة للمجموعة", callback_data="group_send")],
        [InlineKeyboardButton(text="📌 تثبيت رسالة", callback_data="group_pin")],
        [InlineKeyboardButton(text="🗑️ حذف رسالة", callback_data="group_delete")],
        [InlineKeyboardButton(text="◀️ رجوع", callback_data="admin_back")]
    ])
    await callback.message.edit_text("📌 *إدارة المجموعة*", parse_mode="Markdown", reply_markup=keyboard)

# ---------- المعالج الرئيسي لجميع الأزرار (لوحة الأدمن + السوق) ----------
async def process_callback(callback: CallbackQuery):
    await callback.answer()
    data = callback.data
    admin_id = callback.from_user.id
    chat_id = callback.message.chat.id
    admin_name = callback.from_user.full_name

    # أزرار السوق (تم نقلها هنا)
    if data.startswith("shop_page_") or data.startswith("buy_") or data in ["close_shop", "my_ranks"]:
        from _core.events import handle_shop_callback
        await handle_shop_callback(callback)
        return

    # الأزرار التي لا تحتاج صلاحيات
    if data.startswith(("users_page_", "admin_show_", "add_", "sub_", "mute_", "unmute_", "ban_", "unban_", "kick_", "title_", "user_log_")):
        # سيتم معالجتها لاحقاً
        pass
    elif admin_id not in ADMIN_IDS:
        await callback.message.answer("❌ غير مصرح.")
        return

    # ----- أزرار لوحة الأدمن الرئيسية -----
    if data == "admin_users":
        await show_users_list(callback, 1)
        return
    if data == "admin_economy":
        total = await db.fetchval("SELECT SUM(money) FROM users") or 0
        count = await db.fetchval("SELECT COUNT(*) FROM users") or 0
        text = f"💰 *الاقتصاد*\nإجمالي الأموال: {total} {CURRENCY_NAME}\nعدد المستخدمين: {count}"
        await callback.message.edit_text(text, parse_mode="Markdown")
        back = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ رجوع", callback_data="admin_back")]])
        await callback.message.edit_reply_markup(reply_markup=back)
        return
    if data == "admin_titles":
        await show_titles_management(callback)
        return
    if data == "admin_mods":
        await show_mods_list(callback)
        return
    if data == "admin_games":
        await show_game_settings(callback)
        return
    if data == "admin_broadcast":
        await callback.message.edit_text("📣 أرسل نص الإعلان الآن (سيتم إرساله لجميع المستخدمين).")
        # يمكن تفعيل FSM هنا
        back = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ رجوع", callback_data="admin_back")]])
        await callback.message.edit_reply_markup(reply_markup=back)
        return
    if data == "admin_advanced_stats":
        await advanced_stats(callback)
        return
    if data == "admin_group":
        await group_management(callback)
        return
    if data == "admin_shop":
        await show_shop_management(callback)
        return
    if data == "admin_settings":
        await callback.message.edit_text("⚙️ *الإعدادات العامة*\nيمكنك لاحقاً تعديل قيمة XP، المدة، إلخ.")
        back = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ رجوع", callback_data="admin_back")]])
        await callback.message.edit_reply_markup(reply_markup=back)
        return
    if data == "admin_close":
        await callback.message.delete()
        return
    if data == "admin_back":
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="👥 إدارة الأعضاء", callback_data="admin_users")],
            [InlineKeyboardButton(text="💰 الاقتصاد", callback_data="admin_economy")],
            [InlineKeyboardButton(text="🏷️ إدارة الألقاب", callback_data="admin_titles")],
            [InlineKeyboardButton(text="🛡️ المشرفون", callback_data="admin_mods")],
            [InlineKeyboardButton(text="🎮 إعدادات الألعاب", callback_data="admin_games")],
            [InlineKeyboardButton(text="📣 إعلان جماعي", callback_data="admin_broadcast")],
            [InlineKeyboardButton(text="📊 إحصائيات متقدمة", callback_data="admin_advanced_stats")],
            [InlineKeyboardButton(text="📌 إدارة المجموعة", callback_data="admin_group")],
            [InlineKeyboardButton(text="🏪 إدارة السوق", callback_data="admin_shop")],
            [InlineKeyboardButton(text="⚙️ الإعدادات العامة", callback_data="admin_settings")],
            [InlineKeyboardButton(text="❌ إغلاق", callback_data="admin_close")]
        ])
        await callback.message.edit_text("👑 *لوحة تحكم الأدمن المتكاملة*", parse_mode="Markdown", reply_markup=keyboard)
        return

    # ----- إدارة الأعضاء -----
    if data.startswith("users_page_"):
        page = int(data.split("_")[-1])
        await show_users_list(callback, page)
        return
    if data.startswith("admin_show_"):
        target_id = int(data.split("_")[-1])
        await show_user_controls(callback, target_id)
        return
    if data.startswith("user_log_"):
        target_id = int(data.split("_")[-1])
        await show_user_log(callback, target_id)
        return

    # إجراءات التعديل على العضو
    target_id = None
    if data.startswith("add_"):
        parts = data.split("_")
        target_id = int(parts[1])
        amount = int(parts[2])
        target = await get_user(target_id)
        await update_user_money(target_id, amount, "إضافة من اللوحة", admin_id)
        await callback.message.answer(f"✅ تم إضافة {amount} {CURRENCY_NAME}")
        await send_admin_notification(chat_id, admin_name, target['full_name'], "💰 إضافة رصيد", f"+{amount} {CURRENCY_NAME}")
        await show_user_controls(callback, target_id)
        return
    if data.startswith("sub_"):
        parts = data.split("_")
        target_id = int(parts[1])
        amount = int(parts[2])
        target = await get_user(target_id)
        await update_user_money(target_id, -amount, "خصم من اللوحة", admin_id)
        await callback.message.answer(f"✅ تم خصم {amount} {CURRENCY_NAME}")
        await send_admin_notification(chat_id, admin_name, target['full_name'], "💰 خصم رصيد", f"-{amount} {CURRENCY_NAME}")
        await show_user_controls(callback, target_id)
        return
    if data.startswith("mute_"):
        target_id = int(data.split("_")[1])
        target = await get_user(target_id)
        await set_user_status(target_id, "muted")
        await callback.message.answer("🔇 تم الكتم")
        await send_admin_notification(chat_id, admin_name, target['full_name'], "🔇 كتم", "")
        await show_user_controls(callback, target_id)
        return
    if data.startswith("unmute_"):
        target_id = int(data.split("_")[1])
        target = await get_user(target_id)
        await set_user_status(target_id, "active")
        await callback.message.answer("🔈 تم فك الكتم")
        await send_admin_notification(chat_id, admin_name, target['full_name'], "🔈 فك كتم", "")
        await show_user_controls(callback, target_id)
        return
    if data.startswith("ban_"):
        target_id = int(data.split("_")[1])
        target = await get_user(target_id)
        await set_user_status(target_id, "banned")
        await callback.message.answer("🚫 تم الحظر")
        await send_admin_notification(chat_id, admin_name, target['full_name'], "🚫 حظر", "")
        await show_user_controls(callback, target_id)
        return
    if data.startswith("unban_"):
        target_id = int(data.split("_")[1])
        target = await get_user(target_id)
        await set_user_status(target_id, "active")
        await callback.message.answer("✅ تم فك الحظر")
        await send_admin_notification(chat_id, admin_name, target['full_name'], "✅ فك حظر", "")
        await show_user_controls(callback, target_id)
        return
    if data.startswith("kick_"):
        target_id = int(data.split("_")[1])
        target = await get_user(target_id)
        await callback.message.answer("🗑️ تم الطرد")
        await send_admin_notification(chat_id, admin_name, target['full_name'], "🗑️ طرد", "")
        try:
            await callback.message.chat.ban_member(target_id)
            await callback.message.chat.unban_member(target_id)
        except:
            pass
        await show_user_controls(callback, target_id)
        return
    if data.startswith("title_"):
        target_id = int(data.split("_")[1])
        await callback.message.answer(f"أرسل اللقب الجديد للمستخدم (ID: {target_id}) في رسالة منفردة.")
        # يمكن إضافة FSM هنا
        return

def register_callback_handlers(dp: Dispatcher):
    dp.message.register(admin_panel, Command("adminiq"))
    dp.callback_query.register(process_callback)
