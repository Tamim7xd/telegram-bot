from aiogram import Dispatcher
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import Command
from config import ADMIN_IDS, CURRENCY_NAME
from db import db
from _core.users import get_user, update_user_money, set_user_status
from _core.titles import set_user_title
from _core.notify import bot
from datetime import datetime

async def send_admin_notification(chat_id, admin_name, target_name, action, detail=""):
    text = f"🔔 *{action}*\n👤 المشرف: {admin_name}\n👥 المستخدم: {target_name}\n📝 {detail}"
    await bot.send_message(chat_id, text, parse_mode="Markdown")

async def admin_panel(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.reply("⚠️ للأدمن فقط.")
        return
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👥 الأعضاء", callback_data="admin_users")],
        [InlineKeyboardButton(text="💰 الاقتصاد", callback_data="admin_economy")],
        [InlineKeyboardButton(text="📊 إحصائيات", callback_data="admin_stats")],
        [InlineKeyboardButton(text="❌ إغلاق", callback_data="admin_close")]
    ])
    await message.reply("👑 لوحة الأدمن", reply_markup=kb)

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

async def process_callback(callback: CallbackQuery):
    await callback.answer()
    data = callback.data
    admin_id = callback.from_user.id
    if admin_id not in ADMIN_IDS and not data.startswith(("user_","users_page_","admin_back")):
        await callback.message.answer("غير مصرح")
        return
    if data.startswith("users_page_"):
        page = int(data.split("_")[-1])
        await show_users(callback, page)
        return
    if data == "admin_users":
        await show_users(callback, 1)
        return
    if data == "admin_economy":
        total = await db.fetchval("SELECT SUM(money) FROM users") or 0
        count = await db.fetchval("SELECT COUNT(*) FROM users") or 0
        await callback.message.edit_text(f"💰 إجمالي الأموال: {total}\n👥 عدد المستخدمين: {count}")
        back = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ رجوع", callback_data="admin_back")]])
        await callback.message.edit_reply_markup(reply_markup=back)
        return
    if data == "admin_stats":
        msgs = await db.fetchval("SELECT SUM(messages_count) FROM users") or 0
        wins = await db.fetchval("SELECT SUM(wins) FROM users") or 0
        await callback.message.edit_text(f"📊 إحصائيات\nالرسائل: {msgs}\nالانتصارات: {wins}")
        back = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ رجوع", callback_data="admin_back")]])
        await callback.message.edit_reply_markup(reply_markup=back)
        return
    if data == "admin_close":
        await callback.message.delete()
        return
    if data == "admin_back":
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="👥 الأعضاء", callback_data="admin_users")],
            [InlineKeyboardButton(text="💰 الاقتصاد", callback_data="admin_economy")],
            [InlineKeyboardButton(text="📊 إحصائيات", callback_data="admin_stats")],
            [InlineKeyboardButton(text="❌ إغلاق", callback_data="admin_close")]
        ])
        await callback.message.edit_text("👑 لوحة الأدمن", reply_markup=kb)
        return
    if data.startswith("user_"):
        uid = int(data.split("_")[1])
        await show_user_controls(callback, uid)
        return

    # عمليات التحكم
    if data.startswith("add_"):
        _, uid, amt = data.split("_")
        uid, amt = int(uid), int(amt)
        target = await get_user(uid)
        await update_user_money(uid, amt, "إضافة من اللوحة", admin_id)
        await callback.message.answer(f"✅ +{amt}")
        await send_admin_notification(callback.message.chat.id, callback.from_user.full_name, target['full_name'], "💰 إضافة رصيد", f"+{amt}")
        await show_user_controls(callback, uid)
    elif data.startswith("sub_"):
        _, uid, amt = data.split("_")
        uid, amt = int(uid), int(amt)
        target = await get_user(uid)
        await update_user_money(uid, -amt, "خصم من اللوحة", admin_id)
        await callback.message.answer(f"✅ -{amt}")
        await send_admin_notification(callback.message.chat.id, callback.from_user.full_name, target['full_name'], "💰 خصم رصيد", f"-{amt}")
        await show_user_controls(callback, uid)
    elif data.startswith("mute_"):
        uid = int(data.split("_")[1])
        target = await get_user(uid)
        await set_user_status(uid, "muted")
        await callback.message.answer("🔇 تم الكتم")
        await send_admin_notification(callback.message.chat.id, callback.from_user.full_name, target['full_name'], "🔇 كتم", "")
        await show_user_controls(callback, uid)
    elif data.startswith("unmute_"):
        uid = int(data.split("_")[1])
        target = await get_user(uid)
        await set_user_status(uid, "active")
        await callback.message.answer("🔈 فك الكتم")
        await send_admin_notification(callback.message.chat.id, callback.from_user.full_name, target['full_name'], "🔈 فك كتم", "")
        await show_user_controls(callback, uid)
    elif data.startswith("ban_"):
        uid = int(data.split("_")[1])
        target = await get_user(uid)
        await set_user_status(uid, "banned")
        await callback.message.answer("🚫 تم الحظر")
        await send_admin_notification(callback.message.chat.id, callback.from_user.full_name, target['full_name'], "🚫 حظر", "")
        await show_user_controls(callback, uid)
    elif data.startswith("unban_"):
        uid = int(data.split("_")[1])
        target = await get_user(uid)
        await set_user_status(uid, "active")
        await callback.message.answer("✅ فك الحظر")
        await show_user_controls(callback, uid)
    elif data.startswith("kick_"):
        uid = int(data.split("_")[1])
        target = await get_user(uid)
        await callback.message.answer("🗑️ تم الطرد")
        await send_admin_notification(callback.message.chat.id, callback.from_user.full_name, target['full_name'], "🗑️ طرد", "")
        try:
            await callback.message.chat.ban_member(uid)
            await callback.message.chat.unban_member(uid)
        except: pass
        await show_user_controls(callback, uid)
    elif data.startswith("title_"):
        uid = int(data.split("_")[1])
        await callback.message.answer(f"أرسل اللقب الجديد للمستخدم {uid} في رسالة منفردة.")

def register_callback_handlers(dp: Dispatcher):
    dp.message.register(admin_panel, Command("adminiq"))
    dp.callback_query.register(process_callback)
