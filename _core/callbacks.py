from aiogram import Dispatcher
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import Command
from config import ADMIN_IDS, CURRENCY_NAME
from db import db
from _core.users import get_user, update_user_money, set_user_status, is_admin, is_general_mod, is_admin_mod, add_general_mod, remove_general_mod, add_admin_mod, remove_admin_mod, get_user_warnings_list, reset_warnings, add_warning
from _core.titles import set_user_title
from _core.notify import bot, send_auto_delete, send_deduction_notification, send_reward_notification, send_warning_notification, send_admin_notification
import asyncio

def format_number(num):
    return f"{num:,}".replace(",", " ").replace(",", ".")

# حالة مؤقتة لانتظار إدخال اللقب من الأدمن
temp_data = {}

async def admin_panel(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("⚠️ هذه اللوحة للأدمن فقط.")
        return
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👥 إدارة الأعضاء", callback_data="admin_users")],
        [InlineKeyboardButton(text="💰 الاقتصاد", callback_data="admin_economy")],
        [InlineKeyboardButton(text="📊 الإحصائيات", callback_data="admin_stats")],
        [InlineKeyboardButton(text="🛡️ إدارة المشرفين", callback_data="admin_mods")],
        [InlineKeyboardButton(text="⚠️ التحذيرات", callback_data="admin_warnings")],
        [InlineKeyboardButton(text="🏪 إدارة السوق", callback_data="admin_shop")],
        [InlineKeyboardButton(text="📋 سجل الإدارة", callback_data="admin_logs")],
        [InlineKeyboardButton(text="❌ إغلاق", callback_data="admin_close")]
    ])
    await message.reply("👑 *لوحة تحكم الأدمن*", reply_markup=kb, parse_mode="Markdown")

# ====== عرض الأعضاء مع رتبهم ======
async def show_users(callback: CallbackQuery, page=1):
    limit = 10
    off = (page-1)*limit
    rows = await db.fetch("SELECT telegram_id, full_name, money, level, warnings FROM users ORDER BY created_at DESC LIMIT ? OFFSET ?", limit, off)
    if not rows:
        await callback.message.edit_text("لا يوجد أعضاء")
        return
    text = "👥 *الأعضاء*\n\n"
    btns = []
    for r in rows:
        # تحديد الرتبة
        is_gen = await is_general_mod(r['telegram_id'])
        is_adm_mod = await is_admin_mod(r['telegram_id'])
        if is_adm_mod:
            role_icon = "⚜️"
            role_text = "مشرف إداري"
        elif is_gen:
            role_icon = "🛡️"
            role_text = "مشرف عادي"
        else:
            role_icon = "👤"
            role_text = "عضو"
        text += f"{role_icon} {r['full_name']} - {role_text}\n💰 {format_number(r['money'])} - مستوى {r['level']} - ⚠️ {r['warnings']}/100\n"
        btns.append([InlineKeyboardButton(text=f"{r['full_name']} ({role_text})", callback_data=f"user_{r['telegram_id']}")])
    nav = []
    if page>1:
        nav.append(InlineKeyboardButton(text="◀️ السابق", callback_data=f"users_page_{page-1}"))
    if len(rows)==limit:
        nav.append(InlineKeyboardButton(text="▶️ التالي", callback_data=f"users_page_{page+1}"))
    if nav:
        btns.append(nav)
    btns.append([InlineKeyboardButton(text="◀️ رجوع", callback_data="admin_back")])
    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=btns), parse_mode="Markdown")

async def show_user_controls(callback: CallbackQuery, uid):
    user = await get_user(uid)
    if not user:
        await callback.answer("المستخدم غير موجود")
        return
    text = f"👤 *{user['full_name']}*\n💰 الرصيد: {format_number(user['money'])}\n⭐ XP: {user['xp']}\n📊 المستوى: {user['level']}\n🏷️ اللقب: {user['title'] or 'لا يوجد'}\n⚠️ التحذيرات: {user['warnings']}/100"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ +100", callback_data=f"add_{uid}_100"),
         InlineKeyboardButton(text="➖ -50", callback_data=f"sub_{uid}_50")],
        [InlineKeyboardButton(text="⚠️ تحذير", callback_data=f"warn_{uid}"),
         InlineKeyboardButton(text="⚠️ إعادة تعيين التحذيرات", callback_data=f"reset_warns_{uid}")],
        [InlineKeyboardButton(text="🏷️ تغيير اللقب", callback_data=f"title_req_{uid}")],
        [InlineKeyboardButton(text="📜 سجل العمليات", callback_data=f"user_log_{uid}")],
        [InlineKeyboardButton(text="◀️ رجوع", callback_data="admin_users")]
    ])
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")

async def show_user_log(callback: CallbackQuery, uid):
    rows = await db.fetch("SELECT * FROM economy_log WHERE user_id = ? ORDER BY timestamp DESC LIMIT 15", uid)
    if not rows:
        await callback.message.edit_text("لا توجد عمليات لهذا المستخدم.")
        return
    text = "📜 *سجل عمليات المستخدم*\n\n"
    for r in rows:
        admin = await get_user(r['admin_id']) if r['admin_id'] else None
        admin_name = admin['full_name'] if admin else "نظام"
        text += f"• {format_number(r['amount'])} {CURRENCY_NAME} - {r['reason']} (بواسطة {admin_name}) - {r['timestamp']}\n"
    back = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ رجوع", callback_data=f"user_{uid}")]])
    await callback.message.edit_text(text, reply_markup=back, parse_mode="Markdown")

# ====== إدارة المشرفين (رفع مشرف من قائمة الأعضاء) ======
async def manage_mods(callback: CallbackQuery):
    # عرض قائمة الأعضاء لاختيار من نرفعه مشرفاً
    rows = await db.fetch("SELECT telegram_id, full_name FROM users ORDER BY created_at DESC LIMIT 20")
    if not rows:
        await callback.message.edit_text("لا يوجد أعضاء.")
        return
    text = "🛡️ *اختر العضو لرفعه مشرفاً:*\n"
    btns = []
    for r in rows:
        btns.append([InlineKeyboardButton(text=r['full_name'], callback_data=f"promote_{r['telegram_id']}")])
    btns.append([InlineKeyboardButton(text="◀️ رجوع", callback_data="admin_back")])
    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=btns), parse_mode="Markdown")

async def promote_user_to(callback: CallbackQuery, user_id, role):
    if role == "general":
        await add_general_mod(user_id, callback.from_user.id)
        role_name = "مشرف عادي"
    else:
        await add_admin_mod(user_id, callback.from_user.id)
        role_name = "مشرف إداري"
    user = await get_user(user_id)
    await callback.message.edit_text(f"✅ تم رفع {user['full_name']} إلى {role_name}")
    await send_admin_notification(callback.from_user.full_name, user['full_name'], f"رفع {role_name}", "")

# ====== إدارة التحذيرات ======
async def show_all_warnings(callback: CallbackQuery, page=1):
    limit = 10
    off = (page-1)*limit
    rows = await db.fetch("SELECT telegram_id, full_name, warnings FROM users WHERE warnings > 0 ORDER BY warnings DESC LIMIT ? OFFSET ?", limit, off)
    if not rows:
        await callback.message.edit_text("لا يوجد أعضاء لديهم تحذيرات.")
        return
    text = "⚠️ *قائمة التحذيرات*\n\n"
    btns = []
    for r in rows:
        text += f"• {r['full_name']} - ⚠️ {r['warnings']}/100\n"
        btns.append([InlineKeyboardButton(text=f"{r['full_name']} ({r['warnings']})", callback_data=f"warn_details_{r['telegram_id']}")])
    nav = []
    if page>1:
        nav.append(InlineKeyboardButton(text="◀️ السابق", callback_data=f"warns_page_{page-1}"))
    if len(rows)==limit:
        nav.append(InlineKeyboardButton(text="▶️ التالي", callback_data=f"warns_page_{page+1}"))
    if nav:
        btns.append(nav)
    btns.append([InlineKeyboardButton(text="◀️ رجوع", callback_data="admin_back")])
    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=btns), parse_mode="Markdown")

async def show_warnings_details(callback: CallbackQuery, uid):
    user = await get_user(uid)
    if not user:
        await callback.answer("المستخدم غير موجود")
        return
    warns = await get_user_warnings_list(uid, 10)
    if not warns:
        await callback.message.edit_text(f"⚠️ {user['full_name']} ليس لديه تحذيرات.")
        return
    text = f"⚠️ *تحذيرات {user['full_name']}* (إجمالي {user['warnings']}/100)\n\n"
    for i, w in enumerate(warns, 1):
        admin = await get_user(w['admin_id'])
        admin_name = admin['full_name'] if admin else "نظام"
        text += f"{i}. {w['reason']} (بواسطة {admin_name}) - {w['created_at']}\n"
    back = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ رجوع", callback_data="admin_warnings")]])
    await callback.message.edit_text(text, reply_markup=back, parse_mode="Markdown")

# ====== إدارة السوق ======
async def manage_shop(callback: CallbackQuery):
    items = await db.fetch("SELECT id, name, price, rank_level FROM shop_items ORDER BY rank_level")
    text = "🏪 *إدارة السوق*\n\n"
    if items:
        for it in items:
            text += f"🆔 {it['id']} - {it['name']} - 💰{format_number(it['price'])} - مستوى {it['rank_level']}\n"
    else:
        text += "لا توجد منتجات.\n"
    text += "\n*الأوامر النصية لإدارة السوق (تُكتب في الخاص):*\n"
    text += "`$إضافة منتج <الاسم> | <السعر> | <المستوى>`\n"
    text += "`$تعديل سعر <id> | <السعر الجديد>`\n"
    text += "`$حذف منتج <id>`"
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ رجوع", callback_data="admin_back")]])
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")

# ====== سجل الإدارة ======
async def show_admin_logs(callback: CallbackQuery, page=1):
    limit = 15
    off = (page-1)*limit
    rows = await db.fetch("SELECT * FROM economy_log ORDER BY timestamp DESC LIMIT ? OFFSET ?", limit, off)
    if not rows:
        await callback.message.edit_text("لا توجد عمليات مسجلة.")
        return
    text = "📜 *سجل الإدارة*\n\n"
    for r in rows:
        admin = await get_user(r['admin_id']) if r['admin_id'] else None
        admin_name = admin['full_name'] if admin else "نظام"
        user = await get_user(r['user_id'])
        user_name = user['full_name'] if user else "غير معروف"
        text += f"• {format_number(r['amount'])} {CURRENCY_NAME} للمستخدم {user_name} - {r['reason']} (بواسطة {admin_name})\n"
    nav = []
    if page>1:
        nav.append(InlineKeyboardButton(text="◀️ السابق", callback_data=f"logs_page_{page-1}"))
    if len(rows)==limit:
        nav.append(InlineKeyboardButton(text="▶️ التالي", callback_data=f"logs_page_{page+1}"))
    nav.append(InlineKeyboardButton(text="◀️ رجوع", callback_data="admin_back"))
    kb = InlineKeyboardMarkup(inline_keyboard=[nav] if nav else [])
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")

# ====== المعالج الرئيسي ======
async def process_callback(callback: CallbackQuery):
    await callback.answer()
    data = callback.data
    uid = callback.from_user.id
    if uid not in ADMIN_IDS:
        await callback.message.answer("غير مصرح")
        return
    admin_name = callback.from_user.full_name
    chat_id = callback.message.chat.id

    # التنقل
    if data.startswith("users_page_"):
        page = int(data.split("_")[-1])
        await show_users(callback, page)
    elif data.startswith("warns_page_"):
        page = int(data.split("_")[-1])
        await show_all_warnings(callback, page)
    elif data.startswith("logs_page_"):
        page = int(data.split("_")[-1])
        await show_admin_logs(callback, page)

    elif data == "admin_back":
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="👥 إدارة الأعضاء", callback_data="admin_users")],
            [InlineKeyboardButton(text="💰 الاقتصاد", callback_data="admin_economy")],
            [InlineKeyboardButton(text="📊 الإحصائيات", callback_data="admin_stats")],
            [InlineKeyboardButton(text="🛡️ إدارة المشرفين", callback_data="admin_mods")],
            [InlineKeyboardButton(text="⚠️ التحذيرات", callback_data="admin_warnings")],
            [InlineKeyboardButton(text="🏪 إدارة السوق", callback_data="admin_shop")],
            [InlineKeyboardButton(text="📋 سجل الإدارة", callback_data="admin_logs")],
            [InlineKeyboardButton(text="❌ إغلاق", callback_data="admin_close")]
        ])
        await callback.message.edit_text("👑 *لوحة تحكم الأدمن*", reply_markup=kb, parse_mode="Markdown")
    elif data == "admin_users":
        await show_users(callback, 1)
    elif data == "admin_economy":
        total = await db.fetchval("SELECT SUM(money) FROM users") or 0
        count = await db.fetchval("SELECT COUNT(*) FROM users") or 0
        await callback.message.edit_text(f"💰 *الاقتصاد*\nإجمالي الأموال: {format_number(total)} {CURRENCY_NAME}\n👥 عدد المستخدمين: {count}", parse_mode="Markdown")
        back = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ رجوع", callback_data="admin_back")]])
        await callback.message.edit_reply_markup(reply_markup=back)
    elif data == "admin_stats":
        msgs = await db.fetchval("SELECT SUM(messages_count) FROM users") or 0
        wins = await db.fetchval("SELECT SUM(wins) FROM users") or 0
        await callback.message.edit_text(f"📊 *الإحصائيات*\nالرسائل: {format_number(msgs)}\nالانتصارات: {wins}", parse_mode="Markdown")
        back = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ رجوع", callback_data="admin_back")]])
        await callback.message.edit_reply_markup(reply_markup=back)
    elif data == "admin_mods":
        await manage_mods(callback)
    elif data == "admin_warnings":
        await show_all_warnings(callback, 1)
    elif data == "admin_shop":
        await manage_shop(callback)
    elif data == "admin_logs":
        await show_admin_logs(callback, 1)
    elif data == "admin_close":
        await callback.message.delete()

    elif data.startswith("user_"):
        uid2 = int(data.split("_")[1])
        await show_user_controls(callback, uid2)
    elif data.startswith("warn_details_"):
        uid2 = int(data.split("_")[-1])
        await show_warnings_details(callback, uid2)
    elif data.startswith("user_log_"):
        uid2 = int(data.split("_")[-1])
        await show_user_log(callback, uid2)
    elif data.startswith("reset_warns_"):
        uid2 = int(data.split("_")[-1])
        user = await get_user(uid2)
        await reset_warnings(uid2)
        await callback.message.answer(f"✅ تم إعادة تعيين تحذيرات {user['full_name']} إلى 0")
        await show_user_controls(callback, uid2)
    elif data.startswith("warn_"):
        uid2 = int(data.split("_")[-1])
        reason = "تحذير من لوحة الأدمن"
        new_count = await add_warning(uid2, reason, uid)
        user = await get_user(uid2)
        await callback.message.answer(f"⚠️ تم تحذير {user['full_name']} (التحذير {new_count}/100)")
        await send_warning_notification(chat_id, admin_name, user['full_name'], new_count, reason)
        await show_user_controls(callback, uid2)

    # تغيير اللقب (طلب إدخال اللقب)
    elif data.startswith("title_req_"):
        uid2 = int(data.split("_")[-1])
        # تخزين حالة انتظار
        temp_data[uid] = {"action": "waiting_title", "target": uid2}
        await callback.message.edit_text(f"🏷️ *تغيير اللقب*\nأرسل اللقب الجديد للمستخدم في رسالة نصية عادية:")

    # إضافة مشرفين من خلال قائمة الأعضاء
    elif data.startswith("promote_"):
        uid2 = int(data.split("_")[-1])
        # اختيار نوع المشرف (عادي أو إداري)
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🛡️ مشرف عادي", callback_data=f"promote_general_{uid2}")],
            [InlineKeyboardButton(text="⚜️ مشرف إداري", callback_data=f"promote_admin_{uid2}")],
            [InlineKeyboardButton(text="◀️ رجوع", callback_data="admin_mods")]
        ])
        await callback.message.edit_text(f"اختر نوع المشرف لـ {uid2}:", reply_markup=kb)
    elif data.startswith("promote_general_"):
        uid2 = int(data.split("_")[-1])
        await promote_user_to(callback, uid2, "general")
    elif data.startswith("promote_admin_"):
        uid2 = int(data.split("_")[-1])
        await promote_user_to(callback, uid2, "admin")

    # عمليات تعديل الرصيد
    elif data.startswith("add_"):
        _, uid2, amt = data.split("_")
        uid2, amt = int(uid2), int(amt)
        target = await get_user(uid2)
        await update_user_money(uid2, amt, "إضافة من اللوحة", uid)
        await callback.message.answer(f"✅ +{format_number(amt)}")
        await send_reward_notification(chat_id, admin_name, target['full_name'], amt, "إضافة من لوحة الأدمن")
        await show_user_controls(callback, uid2)
    elif data.startswith("sub_"):
        _, uid2, amt = data.split("_")
        uid2, amt = int(uid2), int(amt)
        target = await get_user(uid2)
        await update_user_money(uid2, -amt, "خصم من اللوحة", uid)
        await callback.message.answer(f"✅ -{format_number(amt)}")
        await send_deduction_notification(chat_id, admin_name, target['full_name'], amt, "خصم من لوحة الأدمن")
        await show_user_controls(callback, uid2)

def register_callback_handlers(dp: Dispatcher):
    dp.message.register(admin_panel, Command("adminiq"))
    dp.callback_query.register(process_callback)
