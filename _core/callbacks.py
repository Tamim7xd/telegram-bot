from aiogram import Dispatcher
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, ChatPermissions
from aiogram.filters import Command
from config import ADMIN_IDS, CURRENCY_NAME, GROUP_ID
from db import db
from _core.users import get_user, update_user_money, set_user_status
from _core.titles import set_user_title
from _core.notify import bot, send_auto_delete, send_admin_notification
import asyncio

async def admin_panel(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("⚠️ للأدمن فقط")
        return
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👥 الأعضاء", callback_data="admin_users")],
        [InlineKeyboardButton(text="💰 الاقتصاد", callback_data="admin_economy")],
        [InlineKeyboardButton(text="📊 الإحصائيات", callback_data="admin_stats")],
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
    text = "👥 الأعضاء:\n"
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
    btns.append([InlineKeyboardButton(text="رجوع", callback_data="admin_back")])
    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=btns))

async def show_user_controls(callback: CallbackQuery, uid):
    user = await get_user(uid)
    if not user:
        await callback.answer("غير موجود")
        return
    text = f"👤 {user['full_name']}\n💰 {user['money']}\n⭐ XP: {user['xp']}\n📊 مستوى {user['level']}\n🏷️ لقب: {user['title'] or 'لا يوجد'}"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ +100", callback_data=f"add_{uid}_100"),
         InlineKeyboardButton(text="➖ -50", callback_data=f"sub_{uid}_50")],
        [InlineKeyboardButton(text="🔇 كتم", callback_data=f"mute_{uid}"),
         InlineKeyboardButton(text="🔈 فك كتم", callback_data=f"unmute_{uid}")],
        [InlineKeyboardButton(text="🚫 حظر", callback_data=f"ban_{uid}"),
         InlineKeyboardButton(text="✅ فك حظر", callback_data=f"unban_{uid}")],
        [InlineKeyboardButton(text="🏷️ لقب", callback_data=f"title_{uid}"),
         InlineKeyboardButton(text="🗑️ طرد", callback_data=f"kick_{uid}")],
        [InlineKeyboardButton(text="رجوع", callback_data="admin_users")]
    ])
    await callback.message.edit_text(text, reply_markup=kb)

async def process_callback(callback: CallbackQuery):
    await callback.answer()
    data = callback.data
    uid = callback.from_user.id
    if uid not in ADMIN_IDS:
        await callback.message.answer("غير مصرح")
        return
    admin_name = callback.from_user.full_name

    if data.startswith("users_page_"):
        page = int(data.split("_")[-1])
        await show_users(callback, page)
    elif data == "admin_users":
        await show_users(callback, 1)
    elif data == "admin_economy":
        total = await db.fetchval("SELECT SUM(money) FROM users") or 0
        count = await db.fetchval("SELECT COUNT(*) FROM users") or 0
        msg = await callback.message.edit_text(f"💰 إجمالي الأموال: {total}\n👥 المستخدمون: {count}")
        back = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="رجوع", callback_data="admin_back")]])
        await msg.edit_reply_markup(reply_markup=back)
    elif data == "admin_stats":
        msgs = await db.fetchval("SELECT SUM(messages_count) FROM users") or 0
        wins = await db.fetchval("SELECT SUM(wins) FROM users") or 0
        msg = await callback.message.edit_text(f"📊 الرسائل: {msgs}\n🏆 الانتصارات: {wins}")
        back = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="رجوع", callback_data="admin_back")]])
        await msg.edit_reply_markup(reply_markup=back)
    elif data == "admin_close":
        await callback.message.delete()
    elif data == "admin_back":
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="👥 الأعضاء", callback_data="admin_users")],
            [InlineKeyboardButton(text="💰 الاقتصاد", callback_data="admin_economy")],
            [InlineKeyboardButton(text="📊 الإحصائيات", callback_data="admin_stats")],
            [InlineKeyboardButton(text="❌ إغلاق", callback_data="admin_close")]
        ])
        await callback.message.edit_text("👑 لوحة الأدمن", reply_markup=kb)
    elif data.startswith("user_"):
        uid2 = int(data.split("_")[1])
        await show_user_controls(callback, uid2)

    # إجراءات التعديل (باستخدام الدوال الصحيحة)
    elif data.startswith("add_"):
        _, uid2, amt = data.split("_")
        uid2, amt = int(uid2), int(amt)
        target = await get_user(uid2)
        await update_user_money(uid2, amt, "إضافة من اللوحة", uid)
        await callback.message.answer(f"✅ +{amt}")
        await send_admin_notification(admin_name, target['full_name'], "💰 إضافة رصيد", f"+{amt}")
        await show_user_controls(callback, uid2)
    elif data.startswith("sub_"):
        _, uid2, amt = data.split("_")
        uid2, amt = int(uid2), int(amt)
        target = await get_user(uid2)
        await update_user_money(uid2, -amt, "خصم من اللوحة", uid)
        await callback.message.answer(f"✅ -{amt}")
        await send_admin_notification(admin_name, target['full_name'], "💰 خصم رصيد", f"-{amt}")
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
        await callback.message.answer(f"أرسل اللقب الجديد للمستخدم {uid2} في رسالة منفردة.")

def register_callback_handlers(dp: Dispatcher):
    dp.message.register(admin_panel, Command("adminiq"))
    dp.callback_query.register(process_callback)
