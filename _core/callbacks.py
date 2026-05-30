from aiogram import Dispatcher
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, ChatPermissions
from aiogram.filters import Command
from config import ADMIN_IDS, CURRENCY_NAME, GROUP_ID
from db import db
from _core.users import get_user, update_user_money, set_user_status, is_admin, is_general_mod, is_admin_mod, add_general_mod, remove_general_mod, add_admin_mod, remove_admin_mod, add_warning, get_user_warnings_list, get_user_warnings_count, reset_warnings
from _core.titles import set_user_title
from _core.notify import bot, send_auto_delete, send_admin_notification
import asyncio

def format_number(num):
    return f"{num:,}".replace(",", " ").replace(",", ".")

# دالة safe_edit معدلة لتقبل parse_mode وتمريره إلى edit_text إذا لزم الأمر
async def safe_edit(callback: CallbackQuery, text: str, reply_markup=None, parse_mode: str = None):
    try:
        # إذا كانت الرسالة الحالية تحمل نفس النص والأزرار، لا نفعل شيئاً
        if callback.message.text == text and callback.message.reply_markup == reply_markup:
            return
        await callback.message.edit_text(text, reply_markup=reply_markup, parse_mode=parse_mode)
    except Exception:
        await callback.message.answer(text, reply_markup=reply_markup, parse_mode=parse_mode)

async def admin_panel(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("⚠️ هذه اللوحة للأدمن فقط.")
        return
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👥 إدارة الأعضاء", callback_data="admin_users")],
        [InlineKeyboardButton(text="💰 الاقتصاد", callback_data="admin_economy")],
        [InlineKeyboardButton(text="📊 الإحصائيات", callback_data="admin_stats")],
        [InlineKeyboardButton(text="🛡️ إدارة المشرفين", callback_data="admin_manage_mods")],
        [InlineKeyboardButton(text="⚠️ إدارة التحذيرات", callback_data="admin_warnings")],
        [InlineKeyboardButton(text="🏪 إدارة السوق", callback_data="admin_shop")],
        [InlineKeyboardButton(text="📋 سجل العمليات", callback_data="admin_logs")],
        [InlineKeyboardButton(text="📣 إعلان جماعي", callback_data="admin_broadcast")],
        [InlineKeyboardButton(text="📌 تثبيت رسالة", callback_data="admin_pin")],
        [InlineKeyboardButton(text="❌ إغلاق", callback_data="admin_close")]
    ])
    await message.reply("👑 *لوحة تحكم الأدمن المتكاملة*", reply_markup=kb, parse_mode="Markdown")

async def show_users(callback: CallbackQuery, page=1):
    limit = 10
    off = (page-1)*limit
    rows = await db.fetch("SELECT telegram_id, full_name, money, level, warnings FROM users ORDER BY created_at DESC LIMIT ? OFFSET ?", limit, off)
    if not rows:
        await safe_edit(callback, "لا يوجد أعضاء")
        return
    text = "👥 *الأعضاء*\n\n"
    btns = []
    for r in rows:
        text += f"• {r['full_name']} - 💰{format_number(r['money'])} - مستوى {r['level']} - ⚠️ {r['warnings']}/100\n"
        btns.append([InlineKeyboardButton(text=r['full_name'], callback_data=f"user_{r['telegram_id']}")])
    nav = []
    if page>1:
        nav.append(InlineKeyboardButton(text="◀️ السابق", callback_data=f"users_page_{page-1}"))
    if len(rows)==limit:
        nav.append(InlineKeyboardButton(text="▶️ التالي", callback_data=f"users_page_{page+1}"))
    if nav:
        btns.append(nav)
    btns.append([InlineKeyboardButton(text="◀️ رجوع", callback_data="admin_back")])
    await safe_edit(callback, text, reply_markup=InlineKeyboardMarkup(inline_keyboard=btns), parse_mode="Markdown")

async def show_user_controls(callback: CallbackQuery, uid):
    user = await get_user(uid)
    if not user:
        await callback.answer("المستخدم غير موجود")
        return
    warns = await get_user_warnings_list(uid, 3)
    warns_text = ""
    for w in warns:
        admin = await get_user(w['admin_id'])
        admin_name = admin['full_name'] if admin else "نظام"
        warns_text += f"• {w['reason']} (بواسطة {admin_name}) - {w['created_at']}\n"
    if not warns_text:
        warns_text = "لا توجد تحذيرات"
    text = f"""👤 *{user['full_name']}*
🆔 المعرف: @{user['username'] or 'لا يوجد'}
━━━━━━━━━━━━━━━━━
💰 الرصيد: {format_number(user['money'])} {CURRENCY_NAME}
⭐ XP: {user['xp']}
📊 المستوى: {user['level']}
🏷️ اللقب: {user['title'] or 'لا يوجد'}
⚠️ التحذيرات: {user['warnings']}/100
━━━━━━━━━━━━━━━━━
⚠️ *آخر التحذيرات:*
{warns_text}
━━━━━━━━━━━━━━━━━"""
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ إضافة 100", callback_data=f"add_{uid}_100"),
         InlineKeyboardButton(text="➖ خصم 50", callback_data=f"sub_{uid}_50")],
        [InlineKeyboardButton(text="🔇 كتم", callback_data=f"mute_{uid}"),
         InlineKeyboardButton(text="🔈 فك كتم", callback_data=f"unmute_{uid}")],
        [InlineKeyboardButton(text="🚫 حظر", callback_data=f"ban_{uid}"),
         InlineKeyboardButton(text="✅ فك حظر", callback_data=f"unban_{uid}")],
        [InlineKeyboardButton(text="🏷️ تغيير اللقب", callback_data=f"title_{uid}"),
         InlineKeyboardButton(text="🗑️ طرد", callback_data=f"kick_{uid}"),
         InlineKeyboardButton(text="⚠️ تحذير فردي", callback_data=f"warn_{uid}")],
        [InlineKeyboardButton(text="⚠️ إعادة تعيين التحذيرات", callback_data=f"reset_warns_{uid}")],
        [InlineKeyboardButton(text="📜 سجل العمليات", callback_data=f"user_log_{uid}")],
        [InlineKeyboardButton(text="◀️ رجوع", callback_data="admin_users")]
    ])
    await safe_edit(callback, text, reply_markup=kb, parse_mode="Markdown")

async def show_user_log(callback: CallbackQuery, uid):
    rows = await db.fetch("SELECT * FROM economy_log WHERE user_id = ? ORDER BY timestamp DESC LIMIT 15", uid)
    if not rows:
        await safe_edit(callback, "لا توجد عمليات لهذا المستخدم.")
        return
    text = "📜 *سجل عمليات المستخدم:*\n\n"
    for r in rows:
        admin = await get_user(r['admin_id']) if r['admin_id'] else None
        admin_name = admin['full_name'] if admin else "نظام"
        text += f"• {format_number(r['amount'])} {CURRENCY_NAME} - {r['reason']} (بواسطة {admin_name}) - {r['timestamp']}\n"
    back = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ رجوع", callback_data=f"user_{uid}")]])
    await safe_edit(callback, text, reply_markup=back, parse_mode="Markdown")

async def show_all_warnings(callback: CallbackQuery, page=1):
    limit = 10
    off = (page-1)*limit
    rows = await db.fetch("SELECT telegram_id, full_name, warnings FROM users WHERE warnings > 0 ORDER BY warnings DESC LIMIT ? OFFSET ?", limit, off)
    if not rows:
        await safe_edit(callback, "لا يوجد أعضاء لديهم تحذيرات.")
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
    await safe_edit(callback, text, reply_markup=InlineKeyboardMarkup(inline_keyboard=btns), parse_mode="Markdown")

async def show_warnings_details(callback: CallbackQuery, uid):
    user = await get_user(uid)
    if not user:
        await callback.answer("المستخدم غير موجود")
        return
    warns = await get_user_warnings_list(uid, 10)
    if not warns:
        await safe_edit(callback, f"⚠️ {user['full_name']} ليس لديه تحذيرات.")
        return
    text = f"⚠️ *تحذيرات {user['full_name']}* (إجمالي {user['warnings']}/100)\n\n"
    for i, w in enumerate(warns, 1):
        admin = await get_user(w['admin_id'])
        admin_name = admin['full_name'] if admin else "نظام"
        text += f"{i}. {w['reason']} (بواسطة {admin_name}) - {w['created_at']}\n"
    back = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ رجوع", callback_data="admin_warnings")]])
    await safe_edit(callback, text, reply_markup=back, parse_mode="Markdown")

async def select_users_for_warning(callback: CallbackQuery, page=1):
    limit = 10
    off = (page-1)*limit
    rows = await db.fetch("SELECT telegram_id, full_name FROM users ORDER BY created_at DESC LIMIT ? OFFSET ?", limit, off)
    if not rows:
        await safe_edit(callback, "لا يوجد أعضاء.")
        return
    text = "⚠️ *اختر عضواً لتحذيره (سيُطلب منك السبب لاحقاً)*\n\n"
    btns = []
    for r in rows:
        btns.append([InlineKeyboardButton(text=r['full_name'], callback_data=f"warn_user_{r['telegram_id']}")])
    nav = []
    if page>1:
        nav.append(InlineKeyboardButton(text="◀️ السابق", callback_data=f"warn_select_page_{page-1}"))
    if len(rows)==limit:
        nav.append(InlineKeyboardButton(text="▶️ التالي", callback_data=f"warn_select_page_{page+1}"))
    if nav:
        btns.append(nav)
    btns.append([InlineKeyboardButton(text="◀️ رجوع", callback_data="admin_back")])
    await safe_edit(callback, text, reply_markup=InlineKeyboardMarkup(inline_keyboard=btns), parse_mode="Markdown")

async def manage_mods(callback: CallbackQuery, page=1):
    limit = 10
    off = (page-1)*limit
    mods = await db.fetch("SELECT user_id, 'general' as type FROM general_mods UNION SELECT user_id, 'admin' as type FROM admin_mods LIMIT ? OFFSET ?", limit, off)
    if not mods:
        await safe_edit(callback, "لا يوجد مشرفون.")
        return
    text = "🛡️ *المشرفون:*\n\n"
    btns = []
    for m in mods:
        u = await get_user(m['user_id'])
        if u:
            type_label = "⚜️ مشرف إداري" if m['type'] == 'admin' else "🛡️ مشرف عادي"
            text += f"{type_label} {u['full_name']} (ID: {m['user_id']})\n"
            btns.append([InlineKeyboardButton(text=f"{type_label} {u['full_name']}", callback_data=f"mod_{m['user_id']}")])
    nav = []
    if page>1:
        nav.append(InlineKeyboardButton(text="◀️ السابق", callback_data=f"mods_page_{page-1}"))
    if len(mods)==limit:
        nav.append(InlineKeyboardButton(text="▶️ التالي", callback_data=f"mods_page_{page+1}"))
    if nav:
        btns.append(nav)
    btns.append([InlineKeyboardButton(text="➕ إضافة مشرف عادي", callback_data="add_mod_general")])
    btns.append([InlineKeyboardButton(text="➕ إضافة مشرف إداري", callback_data="add_mod_admin")])
    btns.append([InlineKeyboardButton(text="◀️ رجوع", callback_data="admin_back")])
    await safe_edit(callback, text, reply_markup=InlineKeyboardMarkup(inline_keyboard=btns), parse_mode="Markdown")

async def show_mod_details(callback: CallbackQuery, uid):
    user = await get_user(uid)
    if not user:
        await callback.answer("المستخدم غير موجود")
        return
    is_gen = await is_general_mod(uid)
    is_adm = await is_admin_mod(uid)
    role = "⚜️ مشرف إداري" if is_adm else ("🛡️ مشرف عادي" if is_gen else "عضو عادي")
    text = f"👤 *{user['full_name']}*\n🆔 المعرف: @{user['username'] or 'لا يوجد'}\n━━━━━━━━━━━━━━━━━\n🎖️ الرتبة: {role}\n💰 الرصيد: {format_number(user['money'])}\n⭐ XP: {user['xp']}\n📊 المستوى: {user['level']}"
    kb = InlineKeyboardMarkup(inline_keyboard=[])
    if is_gen and not is_adm:
        kb.inline_keyboard.append([InlineKeyboardButton(text="⬆️ ترقية إلى مشرف إداري", callback_data=f"promote_to_admin_{uid}")])
        kb.inline_keyboard.append([InlineKeyboardButton(text="❌ حذف المشرف", callback_data=f"demote_{uid}")])
    elif is_adm:
        kb.inline_keyboard.append([InlineKeyboardButton(text="⬇️ تخفيض إلى مشرف عادي", callback_data=f"demote_to_general_{uid}")])
        kb.inline_keyboard.append([InlineKeyboardButton(text="❌ حذف المشرف", callback_data=f"demote_{uid}")])
    else:
        kb.inline_keyboard.append([InlineKeyboardButton(text="➕ رفع مشرف عادي", callback_data=f"make_general_{uid}")])
        kb.inline_keyboard.append([InlineKeyboardButton(text="➕ رفع مشرف إداري", callback_data=f"make_admin_{uid}")])
    kb.inline_keyboard.append([InlineKeyboardButton(text="◀️ رجوع", callback_data="admin_manage_mods")])
    await safe_edit(callback, text, reply_markup=kb, parse_mode="Markdown")

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
    await safe_edit(callback, text, reply_markup=kb, parse_mode="Markdown")

async def show_all_logs(callback: CallbackQuery, page=1):
    limit = 15
    off = (page-1)*limit
    rows = await db.fetch("SELECT * FROM economy_log ORDER BY timestamp DESC LIMIT ? OFFSET ?", limit, off)
    if not rows:
        await safe_edit(callback, "لا توجد عمليات مسجلة.")
        return
    text = "📜 *سجل العمليات العامة*\n\n"
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
    await safe_edit(callback, text, reply_markup=kb, parse_mode="Markdown")

async def pin_message(callback: CallbackQuery):
    await safe_edit(callback, "📌 *تثبيت رسالة*\nأرسل النص الذي تريد تثبيته في المجموعة (أو رد على رسالة موجودة في الخاص).")

async def broadcast_message(callback: CallbackQuery):
    await safe_edit(callback, "📣 *إعلان جماعي*\nأرسل نص الإعلان (سيختفي بعد 30 ثانية).")

async def process_callback(callback: CallbackQuery):
    await callback.answer()
    data = callback.data
    uid = callback.from_user.id
    if uid not in ADMIN_IDS:
        await callback.message.answer("غير مصرح")
        return
    admin_name = callback.from_user.full_name
    chat_id = callback.message.chat.id

    # أزرار التنقل
    if data.startswith("users_page_"):
        page = int(data.split("_")[-1])
        await show_users(callback, page)
    elif data.startswith("warns_page_"):
        page = int(data.split("_")[-1])
        await show_all_warnings(callback, page)
    elif data.startswith("warn_select_page_"):
        page = int(data.split("_")[-1])
        await select_users_for_warning(callback, page)
    elif data.startswith("mods_page_"):
        page = int(data.split("_")[-1])
        await manage_mods(callback, page)
    elif data.startswith("logs_page_"):
        page = int(data.split("_")[-1])
        await show_all_logs(callback, page)

    # الأزرار الرئيسية
    elif data == "admin_back":
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="👥 إدارة الأعضاء", callback_data="admin_users")],
            [InlineKeyboardButton(text="💰 الاقتصاد", callback_data="admin_economy")],
            [InlineKeyboardButton(text="📊 الإحصائيات", callback_data="admin_stats")],
            [InlineKeyboardButton(text="🛡️ إدارة المشرفين", callback_data="admin_manage_mods")],
            [InlineKeyboardButton(text="⚠️ إدارة التحذيرات", callback_data="admin_warnings")],
            [InlineKeyboardButton(text="🏪 إدارة السوق", callback_data="admin_shop")],
            [InlineKeyboardButton(text="📋 سجل العمليات", callback_data="admin_logs")],
            [InlineKeyboardButton(text="📣 إعلان جماعي", callback_data="admin_broadcast")],
            [InlineKeyboardButton(text="📌 تثبيت رسالة", callback_data="admin_pin")],
            [InlineKeyboardButton(text="❌ إغلاق", callback_data="admin_close")]
        ])
        await safe_edit(callback, "👑 *لوحة تحكم الأدمن المتكاملة*", reply_markup=kb, parse_mode="Markdown")
    elif data == "admin_users":
        await show_users(callback, 1)
    elif data == "admin_economy":
        total = await db.fetchval("SELECT SUM(money) FROM users") or 0
        count = await db.fetchval("SELECT COUNT(*) FROM users") or 0
        await safe_edit(callback, f"💰 *الاقتصاد*\nإجمالي الأموال: {format_number(total)} {CURRENCY_NAME}\n👥 عدد المستخدمين: {count}", parse_mode="Markdown")
        back = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ رجوع", callback_data="admin_back")]])
        await callback.message.edit_reply_markup(reply_markup=back)
    elif data == "admin_stats":
        msgs = await db.fetchval("SELECT SUM(messages_count) FROM users") or 0
        wins = await db.fetchval("SELECT SUM(wins) FROM users") or 0
        await safe_edit(callback, f"📊 *الإحصائيات*\nالرسائل: {format_number(msgs)}\nالانتصارات: {wins}", parse_mode="Markdown")
        back = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ رجوع", callback_data="admin_back")]])
        await callback.message.edit_reply_markup(reply_markup=back)
    elif data == "admin_manage_mods":
        await manage_mods(callback, 1)
    elif data == "admin_warnings":
        await show_all_warnings(callback, 1)
    elif data == "admin_shop":
        await manage_shop(callback)
    elif data == "admin_logs":
        await show_all_logs(callback, 1)
    elif data == "admin_broadcast":
        await broadcast_message(callback)
    elif data == "admin_pin":
        await pin_message(callback)
    elif data == "admin_close":
        await callback.message.delete()

    # أزرار الأعضاء
    elif data.startswith("user_"):
        uid2 = int(data.split("_")[1])
        await show_user_controls(callback, uid2)
    elif data.startswith("warn_details_"):
        uid2 = int(data.split("_")[-1])
        await show_warnings_details(callback, uid2)
    elif data.startswith("warn_user_"):
        uid2 = int(data.split("_")[-1])
        await callback.message.answer(f"⚠️ *تحذير عضو*\nأرسل سبب التحذير للمستخدم (ID: {uid2}) في رسالة منفردة (أو 'بدون سبب').")
    elif data.startswith("user_log_"):
        uid2 = int(data.split("_")[-1])
        await show_user_log(callback, uid2)

    # إدارة التحذيرات
    elif data.startswith("reset_warns_"):
        uid2 = int(data.split("_")[-1])
        user = await get_user(uid2)
        await reset_warnings(uid2)
        await callback.message.answer(f"✅ تم إعادة تعيين تحذيرات {user['full_name']} إلى 0.")
        await send_admin_notification(admin_name, user['full_name'], "⚠️ إعادة تعيين التحذيرات", "تم مسح جميع التحذيرات")
        await show_user_controls(callback, uid2)
    elif data.startswith("warn_"):
        uid2 = int(data.split("_")[-1])
        await callback.message.answer(f"⚠️ *تحذير فردي*\nأرسل سبب التحذير للمستخدم (ID: {uid2}) في رسالة منفردة (أو 'بدون سبب').")

    # إدارة المشرفين
    elif data.startswith("mod_"):
        uid2 = int(data.split("_")[-1])
        await show_mod_details(callback, uid2)
    elif data == "add_mod_general":
        await callback.message.answer("➕ *إضافة مشرف عادي*\nأرسل معرف العضو (الرقمي) الذي تريد رفعه مشرفاً عادياً.")
    elif data == "add_mod_admin":
        await callback.message.answer("➕ *إضافة مشرف إداري*\nأرسل معرف العضو (الرقمي) الذي تريد رفعه مشرفاً إدارياً.")
    elif data.startswith("make_general_"):
        uid2 = int(data.split("_")[-1])
        await add_general_mod(uid2, uid)
        user = await get_user(uid2)
        await callback.message.answer(f"✅ تم رفع {user['full_name']} إلى مشرف عادي.")
        await send_admin_notification(admin_name, user['full_name'], "🛡️ رفع مشرف عادي", "")
        await show_mod_details(callback, uid2)
    elif data.startswith("make_admin_"):
        uid2 = int(data.split("_")[-1])
        await add_admin_mod(uid2, uid)
        user = await get_user(uid2)
        await callback.message.answer(f"✅ تم رفع {user['full_name']} إلى مشرف إداري.")
        await send_admin_notification(admin_name, user['full_name'], "⚜️ رفع مشرف إداري", "")
        await show_mod_details(callback, uid2)
    elif data.startswith("promote_to_admin_"):
        uid2 = int(data.split("_")[-1])
        await remove_general_mod(uid2)
        await add_admin_mod(uid2, uid)
        user = await get_user(uid2)
        await callback.message.answer(f"✅ تم ترقية {user['full_name']} إلى مشرف إداري.")
        await send_admin_notification(admin_name, user['full_name'], "⬆️ ترقية إلى مشرف إداري", "")
        await show_mod_details(callback, uid2)
    elif data.startswith("demote_to_general_"):
        uid2 = int(data.split("_")[-1])
        await remove_admin_mod(uid2)
        await add_general_mod(uid2, uid)
        user = await get_user(uid2)
        await callback.message.answer(f"✅ تم تخفيض {user['full_name']} إلى مشرف عادي.")
        await send_admin_notification(admin_name, user['full_name'], "⬇️ تخفيض إلى مشرف عادي", "")
        await show_mod_details(callback, uid2)
    elif data.startswith("demote_"):
        uid2 = int(data.split("_")[-1])
        await remove_general_mod(uid2)
        await remove_admin_mod(uid2)
        user = await get_user(uid2)
        await callback.message.answer(f"✅ تم حذف صلاحيات المشرف عن {user['full_name']}.")
        await send_admin_notification(admin_name, user['full_name'], "❌ إزالة صلاحيات المشرف", "")
        await show_mod_details(callback, uid2)

    # إجراءات التعديل على الرصيد والحظر والكتم
    elif data.startswith("add_"):
        _, uid2, amt = data.split("_")
        uid2, amt = int(uid2), int(amt)
        target = await get_user(uid2)
        await update_user_money(uid2, amt, "إضافة من اللوحة", uid)
        await callback.message.answer(f"✅ +{format_number(amt)}")
        await send_admin_notification(admin_name, target['full_name'], "💰 إضافة رصيد", f"+{format_number(amt)}")
        await show_user_controls(callback, uid2)
    elif data.startswith("sub_"):
        _, uid2, amt = data.split("_")
        uid2, amt = int(uid2), int(amt)
        target = await get_user(uid2)
        await update_user_money(uid2, -amt, "خصم من اللوحة", uid)
        await callback.message.answer(f"✅ -{format_number(amt)}")
        await send_admin_notification(admin_name, target['full_name'], "💰 خصم رصيد", f"-{format_number(amt)}")
        await show_user_controls(callback, uid2)
    elif data.startswith("mute_"):
        uid2 = int(data.split("_")[1])
        target = await get_user(uid2)
        try:
            await callback.message.chat.restrict(uid2, permissions=ChatPermissions(can_send_messages=False))
            await callback.message.answer("🔇 تم كتم")
            await send_admin_notification(admin_name, target['full_name'], "🔇 كتم", "")
            await set_user_status(uid2, "muted")
        except Exception as e:
            await callback.message.answer(f"⚠️ فشل الكتم: {e}")
        await show_user_controls(callback, uid2)
    elif data.startswith("unmute_"):
        uid2 = int(data.split("_")[1])
        target = await get_user(uid2)
        try:
            await callback.message.chat.restrict(uid2, permissions=ChatPermissions(can_send_messages=True, can_send_media_messages=True, can_send_other_messages=True))
            await callback.message.answer("🔈 فك كتم")
            await send_admin_notification(admin_name, target['full_name'], "🔈 فك كتم", "")
            await set_user_status(uid2, "active")
        except Exception as e:
            await callback.message.answer(f"⚠️ فشل فك الكتم: {e}")
        await show_user_controls(callback, uid2)
    elif data.startswith("ban_"):
        uid2 = int(data.split("_")[1])
        target = await get_user(uid2)
        try:
            await callback.message.chat.ban(uid2)
            await callback.message.answer("🚫 تم حظر")
            await send_admin_notification(admin_name, target['full_name'], "🚫 حظر", "")
            await set_user_status(uid2, "banned")
        except Exception as e:
            await callback.message.answer(f"⚠️ فشل الحظر: {e}")
        await show_user_controls(callback, uid2)
    elif data.startswith("unban_"):
        uid2 = int(data.split("_")[1])
        target = await get_user(uid2)
        try:
            await callback.message.chat.unban(uid2)
            await callback.message.answer("✅ فك حظر")
            await send_admin_notification(admin_name, target['full_name'], "✅ فك حظر", "")
            await set_user_status(uid2, "active")
        except Exception as e:
            await callback.message.answer(f"⚠️ فشل فك الحظر: {e}")
        await show_user_controls(callback, uid2)
    elif data.startswith("kick_"):
        uid2 = int(data.split("_")[1])
        target = await get_user(uid2)
        try:
            await callback.message.chat.ban(uid2)
            await callback.message.chat.unban(uid2)
            await callback.message.answer("🗑️ طرد")
            await send_admin_notification(admin_name, target['full_name'], "🗑️ طرد", "")
        except Exception as e:
            await callback.message.answer(f"⚠️ فشل الطرد: {e}")
        await show_user_controls(callback, uid2)
    elif data.startswith("title_"):
        uid2 = int(data.split("_")[1])
        await callback.message.answer(f"🏷️ *تغيير اللقب*\nأرسل اللقب الجديد للمستخدم (ID: {uid2}) في رسالة منفردة.")

async def handle_broadcast_and_pin(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    if message.chat.type != "private":
        return
    if message.reply_to_message and "أرسل نص الإشعار العام" in message.reply_to_message.text:
        await send_auto_delete(GROUP_ID, f"📢 *إعلان عام:*\n{message.text}")
        await message.reply("✅ تم إرسال الإشعار إلى المجموعة")
    elif message.reply_to_message and "أرسل النص الذي تريد تثبيته" in message.reply_to_message.text:
        try:
            sent = await bot.send_message(GROUP_ID, message.text)
            await bot.pin_chat_message(GROUP_ID, sent.message_id)
            await message.reply("✅ تم تثبيت الرسالة")
        except Exception as e:
            await message.reply(f"❌ فشل التثبيت: {e}")

def register_callback_handlers(dp: Dispatcher):
    dp.message.register(admin_panel, Command("adminiq"))
    dp.callback_query.register(process_callback)
    dp.message.register(handle_broadcast_and_pin)
