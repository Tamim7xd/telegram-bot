from aiogram import Dispatcher
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import Command
from config import ADMIN_IDS, CURRENCY_NAME
from db import db
from _core.users import get_user, update_user_money, set_user_status, is_admin, is_general_mod, add_general_mod, remove_general_mod
from _core.titles import set_user_title
from _core.notify import bot, send_auto_delete, send_admin_notification

# ========== لوحة الأدمن الرئيسية ==========
async def admin_panel(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("⚠️ هذه اللوحة للأدمن فقط.")
        return
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👥 إدارة الأعضاء", callback_data="admin_users")],
        [InlineKeyboardButton(text="💰 الاقتصاد", callback_data="admin_economy")],
        [InlineKeyboardButton(text="📊 الإحصائيات", callback_data="admin_stats")],
        [InlineKeyboardButton(text="🛡️ إدارة المشرفين", callback_data="admin_mods")],
        [InlineKeyboardButton(text="🏪 إدارة السوق", callback_data="admin_shop")],
        [InlineKeyboardButton(text="📣 إشعار عام", callback_data="admin_broadcast")],
        [InlineKeyboardButton(text="📌 إرسال مثبت", callback_data="admin_send_pinned")],
        [InlineKeyboardButton(text="❌ إغلاق", callback_data="admin_close")]
    ])
    await message.reply("👑 *لوحة تحكم الأدمن*", reply_markup=kb, parse_mode="Markdown")

# ========== عرض قائمة الأعضاء ==========
async def show_users(callback: CallbackQuery, page=1):
    limit = 10
    off = (page-1)*limit
    rows = await db.fetch("SELECT telegram_id, full_name, money, level FROM users ORDER BY created_at DESC LIMIT ? OFFSET ?", limit, off)
    if not rows:
        await callback.message.edit_text("لا يوجد أعضاء")
        return
    text = "👥 *الأعضاء*\n"
    btns = []
    for r in rows:
        text += f"• {r['full_name']} - 💰{r['money']} - مستوى {r['level']}\n"
        btns.append([InlineKeyboardButton(text=r['full_name'], callback_data=f"user_{r['telegram_id']}")])
    nav = []
    if page>1:
        nav.append(InlineKeyboardButton(text="◀️", callback_data=f"users_page_{page-1}"))
    if len(rows)==limit:
        nav.append(InlineKeyboardButton(text="▶️", callback_data=f"users_page_{page+1}"))
    if nav:
        btns.append(nav)
    btns.append([InlineKeyboardButton(text="◀️ رجوع", callback_data="admin_back")])
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(inline_keyboard=btns))

async def show_user_controls(callback: CallbackQuery, uid):
    user = await get_user(uid)
    if not user:
        await callback.answer("مستخدم غير موجود")
        return
    text = f"👤 {user['full_name']}\n💰 {user['money']}\n⭐ XP: {user['xp']}\n📊 المستوى: {user['level']}\n🏷️ اللقب: {user['title'] or 'لا يوجد'}"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ +100", callback_data=f"add_{uid}_100"),
         InlineKeyboardButton(text="➖ -50", callback_data=f"sub_{uid}_50")],
        [InlineKeyboardButton(text="🔇 كتم", callback_data=f"mute_{uid}"),
         InlineKeyboardButton(text="🔈 فك كتم", callback_data=f"unmute_{uid}")],
        [InlineKeyboardButton(text="🚫 حظر", callback_data=f"ban_{uid}"),
         InlineKeyboardButton(text="✅ فك حظر", callback_data=f"unban_{uid}")],
        [InlineKeyboardButton(text="🏷️ لقب", callback_data=f"title_{uid}"),
         InlineKeyboardButton(text="🗑️ طرد", callback_data=f"kick_{uid}")],
        [InlineKeyboardButton(text="◀️ رجوع", callback_data="admin_users")]
    ])
    await callback.message.edit_text(text, reply_markup=kb)

async def manage_mods(callback: CallbackQuery):
    mods = await db.fetch("SELECT user_id FROM general_mods")
    text = "🛡️ *المشرفون العامون:*\n"
    for m in mods:
        u = await get_user(m['user_id'])
        text += f"• {u['full_name']} (ID: {m['user_id']})\n"
    text += "\nلإضافة مشرف: استخدم الأمر `$رفع مشرف` بالرد.\nلحذف مشرف: استخدم `$حذف مشرف`."
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ رجوع", callback_data="admin_back")]])
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=kb)

async def manage_shop(callback: CallbackQuery):
    items = await db.fetch("SELECT id, name, price, rank_level FROM shop_items ORDER BY rank_level")
    text = "🏪 *إدارة السوق*\n\n"
    if items:
        for it in items:
            text += f"🆔 {it['id']} - {it['name']} - 💰{it['price']} - مستوى {it['rank_level']}\n"
    else:
        text += "لا توجد منتجات.\n"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ إضافة منتج", callback_data="shop_add")],
        [InlineKeyboardButton(text="✏️ تعديل سعر", callback_data="shop_edit")],
        [InlineKeyboardButton(text="❌ حذف منتج", callback_data="shop_delete")],
        [InlineKeyboardButton(text="◀️ رجوع", callback_data="admin_back")]
    ])
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=kb)

# ========== معالج الأزرار الرئيسي ==========
async def process_callback(callback: CallbackQuery):
    await callback.answer()
    data = callback.data
    user_id = callback.from_user.id
    if user_id not in ADMIN_IDS:
        await callback.message.answer("غير مصرح")
        return
    chat_id = callback.message.chat.id
    admin_name = callback.from_user.full_name

    if data.startswith("users_page_"):
        page = int(data.split("_")[-1])
        await show_users(callback, page)
    elif data == "admin_users":
        await show_users(callback, 1)
    elif data == "admin_economy":
        total = await db.fetchval("SELECT SUM(money) FROM users") or 0
        count = await db.fetchval("SELECT COUNT(*) FROM users") or 0
        msg = await callback.message.edit_text(f"💰 إجمالي الأموال: {total}\n👥 عدد المستخدمين: {count}")
        back = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ رجوع", callback_data="admin_back")]])
        await msg.edit_reply_markup(reply_markup=back)
    elif data == "admin_stats":
        msgs = await db.fetchval("SELECT SUM(messages_count) FROM users") or 0
        wins = await db.fetchval("SELECT SUM(wins) FROM users") or 0
        msg = await callback.message.edit_text(f"📊 إحصائيات\nالرسائل: {msgs}\nالانتصارات: {wins}")
        back = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ رجوع", callback_data="admin_back")]])
        await msg.edit_reply_markup(reply_markup=back)
    elif data == "admin_mods":
        await manage_mods(callback)
    elif data == "admin_shop":
        await manage_shop(callback)
    elif data == "admin_broadcast":
        await callback.message.edit_text("أرسل نص الإشعار العام (سيختفي بعد 30 ثانية)")
        back = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ رجوع", callback_data="admin_back")]])
        await callback.message.edit_reply_markup(reply_markup=back)
    elif data == "admin_send_pinned":
        await callback.message.edit_text("أرسل النص الذي تريد تثبيته في المجموعة")
        back = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ رجوع", callback_data="admin_back")]])
        await callback.message.edit_reply_markup(reply_markup=back)
    elif data == "admin_close":
        await callback.message.delete()
    elif data == "admin_back":
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="👥 إدارة الأعضاء", callback_data="admin_users")],
            [InlineKeyboardButton(text="💰 الاقتصاد", callback_data="admin_economy")],
            [InlineKeyboardButton(text="📊 الإحصائيات", callback_data="admin_stats")],
            [InlineKeyboardButton(text="🛡️ إدارة المشرفين", callback_data="admin_mods")],
            [InlineKeyboardButton(text="🏪 إدارة السوق", callback_data="admin_shop")],
            [InlineKeyboardButton(text="📣 إشعار عام", callback_data="admin_broadcast")],
            [InlineKeyboardButton(text="📌 إرسال مثبت", callback_data="admin_send_pinned")],
            [InlineKeyboardButton(text="❌ إغلاق", callback_data="admin_close")]
        ])
        await callback.message.edit_text("👑 *لوحة تحكم الأدمن*", reply_markup=kb, parse_mode="Markdown")
    elif data.startswith("user_"):
        uid = int(data.split("_")[1])
        await show_user_controls(callback, uid)

    # ========== الإجراءات مع إشعارات المجموعة ==========
    elif data.startswith("add_"):
        _, uid, amt = data.split("_")
        uid, amt = int(uid), int(amt)
        target = await get_user(uid)
        await update_user_money(uid, amt, "إضافة من اللوحة", user_id)
        await callback.message.answer(f"✅ +{amt}")
        await send_admin_notification(chat_id, admin_name, target['full_name'], "💰 إضافة رصيد", f"+{amt}")
        await show_user_controls(callback, uid)
    elif data.startswith("sub_"):
        _, uid, amt = data.split("_")
        uid, amt = int(uid), int(amt)
        target = await get_user(uid)
        await update_user_money(uid, -amt, "خصم من اللوحة", user_id)
        await callback.message.answer(f"✅ -{amt}")
        await send_admin_notification(chat_id, admin_name, target['full_name'], "💰 خصم رصيد", f"-{amt}")
        await show_user_controls(callback, uid)
    elif data.startswith("mute_"):
        uid = int(data.split("_")[1])
        target = await get_user(uid)
        await set_user_status(uid, "muted")
        await callback.message.answer("🔇 تم الكتم")
        await send_admin_notification(chat_id, admin_name, target['full_name'], "🔇 كتم", "")
        await show_user_controls(callback, uid)
    elif data.startswith("unmute_"):
        uid = int(data.split("_")[1])
        target = await get_user(uid)
        await set_user_status(uid, "active")
        await callback.message.answer("🔈 فك الكتم")
        await send_admin_notification(chat_id, admin_name, target['full_name'], "🔈 فك كتم", "")
        await show_user_controls(callback, uid)
    elif data.startswith("ban_"):
        uid = int(data.split("_")[1])
        target = await get_user(uid)
        await set_user_status(uid, "banned")
        await callback.message.answer("🚫 تم الحظر")
        await send_admin_notification(chat_id, admin_name, target['full_name'], "🚫 حظر", "")
        await show_user_controls(callback, uid)
    elif data.startswith("unban_"):
        uid = int(data.split("_")[1])
        target = await get_user(uid)
        await set_user_status(uid, "active")
        await callback.message.answer("✅ فك الحظر")
        await send_admin_notification(chat_id, admin_name, target['full_name'], "✅ فك حظر", "")
        await show_user_controls(callback, uid)
    elif data.startswith("kick_"):
        uid = int(data.split("_")[1])
        target = await get_user(uid)
        await callback.message.answer("🗑️ تم الطرد")
        await send_admin_notification(chat_id, admin_name, target['full_name'], "🗑️ طرد", "")
        try:
            await callback.message.chat.ban_member(uid)
            await callback.message.chat.unban_member(uid)
        except: pass
        await show_user_controls(callback, uid)
    elif data.startswith("title_"):
        uid = int(data.split("_")[1])
        await callback.message.answer(f"أرسل اللقب الجديد للمستخدم {uid} في رسالة منفردة.")

# معالج إدارة السوق نصوص
async def handle_shop_text_commands(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    text = message.text.strip()
    if message.chat.type != "private":
        return
    if message.reply_to_message and message.reply_to_message.text and "أرسل بيانات المنتج" in message.reply_to_message.text:
        parts = text.split("|")
        if len(parts) == 3:
            name, price, level = parts[0].strip(), int(parts[1].strip()), int(parts[2].strip())
            await db.execute("INSERT INTO shop_items (name, price, rank_level, description) VALUES (?, ?, ?, ?)", name, price, level, "منتج")
            await message.reply(f"✅ تم إضافة {name}")
        else:
            await message.reply("❌ استخدم: الاسم | السعر | المستوى")
    elif message.reply_to_message and message.reply_to_message.text and "أرسل id المنتج والسعر الجديد" in message.reply_to_message.text:
        parts = text.split("|")
        if len(parts) == 2:
            pid, new_price = int(parts[0].strip()), int(parts[1].strip())
            await db.execute("UPDATE shop_items SET price = ? WHERE id = ?", new_price, pid)
            await message.reply(f"✅ تم تعديل سعر {pid} إلى {new_price}")
        else:
            await message.reply("❌ استخدم: id | السعر")
    elif message.reply_to_message and message.reply_to_message.text and "أرسل id المنتج للحذف" in message.reply_to_message.text:
        try:
            pid = int(text.strip())
            await db.execute("DELETE FROM shop_items WHERE id = ?", pid)
            await message.reply(f"✅ تم حذف المنتج {pid}")
        except:
            await message.reply("❌ أرسل الرقم فقط")

def register_callback_handlers(dp: Dispatcher):
    dp.message.register(admin_panel, Command("adminiq"))
    dp.callback_query.register(process_callback)
    dp.message.register(handle_shop_text_commands)
